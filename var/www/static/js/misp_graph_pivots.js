/* Native Pivotick providers for transient AIL MISP enrichment. */
(function (host, factory) {
    'use strict';
    const conversion = typeof module === 'object' && module.exports ? require('./misp_graph.js') : host.AILMISPGraph;
    const api = factory(conversion);
    if (typeof module === 'object' && module.exports) {
        module.exports = api;
    }
    if (host) {
        host.AILMISPGraphPivots = api;
    }
})(typeof window === 'undefined' ? null : window, function (conversion) {
    'use strict';

    const dataOf = element => element?.getData?.() || element?.data || {};
    const labels = {onion_lookup: 'Onion Lookup', circl_passivedns: 'CIRCL Passive DNS', circl_passivessl: 'CIRCL Passive SSL', passive_ssh: 'Passive SSH', hashlookup: 'CIRCL Hashlookup', ipasn: 'IPASN History', dns: 'DNS Resolver', reversedns: 'Reverse DNS', extract_url_components: 'URL Components', pgp_keyserver: 'PGP Keyserver'};

    function readableDate(value) {
        if (!value) {
            return '';
        }
        const text = String(value);
        // Provider dates without an offset have no asserted timezone. Preserve it.
        if (/^\d{4}-\d{2}-\d{2}T/.test(text) && !/(Z|[+-]\d{2}:\d{2})$/.test(text)) {
            return text.replace('T', ' ').replace(/ 00:00:00$/, '');
        }
        if (/^\d{8}$/.test(text)) {
            return text.slice(0, 4) + '-' + text.slice(4, 6) + '-' + text.slice(6);
        }
        if (/^\d{4}-\d{2}-\d{2}$/.test(text)) {
            return text;
        }
        const date = new Date(/^\d{10}(\.\d+)?$/.test(text) ? Number(value) * 1000 : value);
        return Number.isNaN(date.getTime()) ? text : date.toISOString().replace('T', ' ').replace(/\.\d{3}Z$/, ' UTC');
    }

    function element(tag, className, text) {
        const node = document.createElement(tag);
        node.className = className || '';
        if (text !== undefined) {
            node.textContent = text;
        }
        return node;
    }

    function inputTypes(node) {
        if (conversion.isExpansionNode(node)) {
            return [];
        }
        const pgp = /^pgp:(key|name|mail):(.+)$/.exec(node.id);
        if (pgp) {
            return pgp[1] === 'mail' ? ['text', 'email'] : ['text'];
        }
        const match = /^(domain|ip|ssh-key|decoded|item)::(.+)$/.exec(node.id);
        if (!match) {
            return [];
        }
        return {domain: match[2].endsWith('.onion') ? ['onion-address', 'url'] : ['domain', 'url'], ip: ['ip-dst'], 'ssh-key': ['ssh-fingerprint', 'ip-dst'], decoded: ['sha1'], item: ['url']}[match[1]];
    }

    function readIcon(className) {
        if (typeof window === 'undefined') {
            return '';
        }
        const glyph = element('i', 'misp-icon ' + className);
        document.body.append(glyph);
        const mask = window.getComputedStyle(glyph).maskImage;
        glyph.remove();
        const embedded = /data:image\/svg\+xml;base64,([A-Za-z0-9+/=]+)/.exec(mask);
        if (!embedded) {
            return '';
        }
        const svg = new DOMParser().parseFromString(atob(embedded[1]), 'image/svg+xml').documentElement;
        if (svg.localName !== 'svg') {
            return '';
        }
        svg.removeAttribute('id');
        svg.querySelectorAll('[id]').forEach(node => node.removeAttribute('id'));
        return svg.outerHTML;
    }

    function nodeIcon(metadata, icons, color) {
        const record = metadata.kind === 'observation' ? icons.objects?.get(metadata.object_name) || icons.object : icons.attributes?.get(metadata.attribute_type || metadata.type) || icons.attribute;
        if (!icons.misp || !record) {
            return icons.misp || record || '';
        }
        const background = /^#[0-9a-f]{6}$/i.test(color) ? color : '#1f1f1f';
        // Draw the record first; the MISP origin badge stays in the foreground.
        return '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 32">' +
            '<g class="misp-record-icon"><svg x="4" y="0" width="28" height="28">' + record + '</svg></g>' +
            '<g class="misp-origin-icon"><circle cx="8" cy="24" r="8" fill="' + background + '"/>' +
            '<svg x="0" y="16" width="16" height="16">' + icons.misp + '</svg></g></svg>';
    }

    function candidates(fragment, graphNodes, icons = {}) {
        const result = {nodes: fragment.nodes.map(node => {
            const icon = nodeIcon(node.data._misp, icons, node.style.color);
            return {...node, data: {...node.data, _misp_details: fragment.details.get(node.id) || []}, style: {...node.style, ...(icon ? {svgIcon: icon} : {})}};
        }), edges: []};
        const ids = new Set(result.nodes.map(node => node.id));
        for (const [id, summaries] of fragment.details) {
            if (!ids.has(id) && graphNodes.has(id)) {
                const node = graphNodes.get(id);
                result.nodes.push({id, data: {label: dataOf(node).label || id, _misp_details: summaries}, style: node.getStyle?.() || {}});
                ids.add(id);
            }
        }
        result.edges = fragment.edges.map(edge => ({...edge, data: {...edge.data, _misp_details: fragment.details.get(edge.id) || []}, style: {edge: {strokeColor: 'var(--pvt-edge-stroke, #94a3b8)', markerEnd: 'arrow'}}}));
        return result;
    }

    class NativePivots {
        constructor(graph, options) {
            this.graph = graph;
            this.options = options;
            this.Pivotick = options.Pivotick || window.Pivotick;
            this.http = options.fetch || window.fetch.bind(window);
            this.originalNodes = new Map(graph.getMutableNodes().filter(node => !conversion.isExpansionNode(node)).map(node => [node.id, node]));
            this.definitions = [];
            this.committed = [];
            this.destroyed = false;
            this.abort = new AbortController();
            this.icons = {objects: new Map(), attributes: new Map()};
            this.pendingMetadata = new Map();
            this.triage = graph.UIManager?.pivotTriage;
            this.originalToastIngest = this.triage?.toastIngest;
            if (this.originalToastIngest) {
                this.toastIngest = (nodes, marked, edges) => {
                    if (!nodes && !edges && this.notifyMetadataIngest()) {
                        return;
                    }
                    return this.originalToastIngest.call(this.triage, nodes, marked, edges);
                };
                this.triage.toastIngest = this.toastIngest;
            }
            this.syncing = false;
            this.automaticSelections = new WeakMap();
            this.originalMark = graph.pivots.mark;
            this.originalMarkAll = graph.pivots.markAll;
            this.mark = (pivotId, id, selected = true) => {
                const set = graph.pivots.candidates(pivotId);
                const row = [...(set?.nodes || []), ...(set?.edges || [])].find(row => row.id === id);
                this.automaticSelections.get(set)?.delete(row);
                this.originalMark.call(graph.pivots, pivotId, id, selected);
                this.reviewSelection(pivotId, set);
            };
            this.markAll = (pivotId, selected = true) => {
                const set = graph.pivots.candidates(pivotId);
                this.automaticSelections.delete(set);
                this.originalMarkAll.call(graph.pivots, pivotId, selected);
                this.reviewSelection(pivotId, set);
            };
            if (this.originalMark) {
                graph.pivots.mark = this.mark;
            }
            if (this.originalMarkAll) {
                graph.pivots.markAll = this.markAll;
            }
            this.originalIngest = graph.pivots.ingest;
            this.ingest = async (pivotId, ...args) => {
                const set = graph.pivots.candidates(pivotId);
                if (pivotId.startsWith('misp:') && set) {
                    this.selectConnections(set);
                }
                const requested = [...(set?.nodes || []).filter(row => row.deduped || row.state === 'marked').map(row => row.raw), ...(set?.edges || []).filter(row => row.state === 'marked').map(row => row.raw), ...(set?.carried || [])];
                // Native ingestion consumes every carried edge incident to an imported
                // node. Only offer connections whose endpoints are being imported;
                // links belonging to unselected rows stay in this Review batch.
                const withheld = [];
                if (pivotId.startsWith('misp:') && set?.carried) {
                    const ready = new Set([...graph.getMutableNodes().map(node => node.id), ...set.nodes.filter(row => row.state === 'marked' && !row.deduped).map(row => row.id)]);
                    set.carried = set.carried.filter(edge => {
                        if (ready.has(String(edge.from)) && ready.has(String(edge.to))) {
                            return true;
                        }
                        withheld.push(edge);
                        return false;
                    });
                }
                const runId = set?.runId;
                if (pivotId.startsWith('misp:') && set?.runId) {
                    this.pendingMetadata.set(set.runId, {pivotId, runId: set.runId, entities: new Map(requested.filter(raw => raw.data?._misp_details?.some(summary => summary.fields.length)).map(raw => [raw.id, raw.data._misp_details]))});
                }
                let outcome;
                try {
                    outcome = await this.originalIngest.call(graph.pivots, pivotId, ...args);
                } catch (error) {
                    this.pendingMetadata.delete(runId);
                    throw error;
                } finally {
                    if (withheld.length && graph.pivots.candidates(pivotId) === set) {
                        set.carried.push(...withheld);
                    }
                }
                if (outcome.status === 'ingested' && !this.destroyed) {
                    const entities = new Map();
                    for (const raw of requested) {
                        const live = graph.getMutableNode(raw.id) || graph.getMutableEdge(raw.id);
                        const accepted = live?.cloneLedger?.().get(pivotId)?.some(claim => claim.runId === outcome.runId);
                        if (accepted && raw.data?._misp_details?.length) {
                            entities.set(raw.id, raw.data._misp_details);
                        }
                    }
                    if (entities.size) {
                        this.committed.push({pivotId, runId: outcome.runId, entities});
                    }
                }
                this.pendingMetadata.delete(runId);
                if (outcome.status === 'ingested') {
                    this.automaticSelections.delete(set);
                }
                return outcome;
            };
            graph.pivots.ingest = this.ingest;
            this.unsubscribe = graph.onVisibleChange(() => this.sync());
            this.unsubscribeHistory = graph.history?.on(() => this.pruneCommitted());
        }

        connectionPlan(set) {
            const roots = (set.origin || []).map(node => node.id);
            if (!roots.length) {
                return [];
            }
            if (roots.some(id => !this.graph.getMutableNode(id))) {
                throw new Error('The original AIL node is no longer in the graph. Restore it before ingesting these results.');
            }
            const rows = new Map(set.nodes.map(row => [row.id, row]));
            const available = new Set([...this.graph.getMutableNodes().map(node => node.id), ...set.nodes.filter(row => row.state !== 'rejected').map(row => row.id)]);
            const adjacency = new Map();
            const link = (from, to, row) => {
                if (!available.has(from) || !available.has(to)) {
                    return;
                }
                for (const [a, b] of [[from, to], [to, from]]) {
                    const links = adjacency.get(a) || [];
                    links.push({id: b, row});
                    adjacency.set(a, links);
                }
            };
            for (const row of set.edges) {
                if (row.state !== 'rejected') {
                    link(String(row.raw.from), String(row.raw.to), row);
                }
            }
            for (const edge of set.carried || []) {
                link(String(edge.from), String(edge.to));
            }
            for (const edge of this.graph.getMutableEdges?.() || []) {
                link(edge.source.id, edge.target.id);
            }
            // A shortest path adds only the connectors a selected result needs,
            // rather than selecting every attribute in its MISP object/component.
            const paths = new Map(roots.map(id => [id, null]));
            const queue = [...roots];
            for (let index = 0; index < queue.length; index++) {
                for (const next of adjacency.get(queue[index]) || []) {
                    if (!paths.has(next.id)) {
                        paths.set(next.id, {parent: queue[index], row: next.row});
                        queue.push(next.id);
                    }
                }
            }
            const targets = [...set.nodes.filter(row => row.state === 'marked' && !row.deduped).map(row => row.id), ...set.edges.filter(row => row.state === 'marked').flatMap(row => [String(row.raw.from), String(row.raw.to)])];
            const required = new Set();
            const included = new Set();
            for (let id of targets) {
                if (!paths.has(id)) {
                    throw new Error('A selected result has no connection to the original AIL node. Restore rejected connecting results or run the expansion again.');
                }
                while (paths.get(id) && !included.has(id)) {
                    included.add(id);
                    const node = rows.get(id);
                    if (node && !node.deduped && !this.graph.getMutableNode(id)) {
                        required.add(node);
                    }
                    const step = paths.get(id);
                    if (step.row) {
                        required.add(step.row);
                    }
                    id = step.parent;
                }
            }
            return [...required];
        }

        selectConnections(set) {
            for (const row of this.automaticSelections.get(set) || []) {
                if (row.state === 'marked') {
                    row.state = 'candidate';
                }
            }
            this.automaticSelections.delete(set);
            const automatic = new Set();
            for (const row of this.connectionPlan(set)) {
                if (row.state !== 'marked') {
                    row.state = 'marked';
                    automatic.add(row);
                }
            }
            this.automaticSelections.set(set, automatic);
        }

        reviewSelection(pivotId, set) {
            if (!pivotId.startsWith('misp:') || !set) {
                return;
            }
            try {
                this.selectConnections(set);
            } catch (error) {
                this.report(error.message, 'warning');
            }
            this.triage?.panes?.get(pivotId)?.paint();
        }

        notifyMetadataIngest() {
            const run = this.graph.history?.entries().find(entry => entry.kind === 'pivot');
            if (!run) {
                return false;
            }
            const contribution = this.pendingMetadata.get(run.id) || this.committed.find(entry => entry.runId === run.id);
            if (!contribution) {
                return false;
            }
            const updated = [...contribution.entities].filter(([id, summaries]) => {
                const node = this.graph.getMutableNode(id);
                return summaries.some(summary => summary.fields.length) && node?.cloneLedger?.().get(contribution.pivotId)?.some(claim => claim.runId === run.id);
            }).length;
            if (!updated) {
                return false;
            }
            this.graph.notifier.success('Updated MISP module details for ' + updated + ' existing ' + (updated === 1 ? 'node' : 'nodes'));
            return true;
        }

        sync() {
            if (this.syncing) {
                return;
            }
            this.syncing = true;
            try {
                let changed = false;
                for (const edge of this.graph.getMutableEdges?.() || []) {
                    if (dataOf(edge)._misp?.kind === 'relationship' && edge.directed !== true) {
                        edge.directed = true;
                        edge.markDirty?.();
                        changed = true;
                    }
                }
                if (changed) {
                    this.graph.onChange();
                }
                this.pruneCommitted();
            } finally {
                this.syncing = false;
            }
        }

        pruneCommitted() {
            const history = this.graph.history;
            if (!history) {
                return;
            }
            const retained = new Set([...history.entries(), ...history.redoable()].map(entry => entry.id));
            this.committed = this.committed.filter(entry => retained.has(entry.runId) || [...entry.entities.keys()].some(id => {
                const live = this.graph.getMutableNode(id) || this.graph.getMutableEdge(id);
                return live?.cloneLedger?.().get(entry.pivotId)?.some(claim => claim.runId === entry.runId);
            }));
        }

        canExpand(node) {
            return this.originalNodes.has(node.id) && inputTypes(node).length > 0 && Boolean(this.graph.getMutableNode(node.id));
        }

        report(message, kind = 'info') {
            this.options.onStatus?.(message, kind);
        }

        async request(url, payload, signal = this.abort.signal) {
            const options = {credentials: 'same-origin', cache: 'no-store', signal, headers: {'Accept': 'application/json'}};
            if (payload !== undefined) {
                options.method = 'POST';
                options.headers['Content-Type'] = 'application/json';
                options.body = JSON.stringify(payload);
            }
            const response = await this.http(url, options);
            let body;
            try {
                body = await response.json();
            } catch (error) {
                throw new Error('Unable to read the response. Reload this page and check that you are still logged in.');
            }
            if (!response.ok || body.status === 'error') {
                throw new Error(body.reason || 'The expansion request failed.');
            }
            return body;
        }

        async load() {
            this.report('Loading MISP expansion modules…');
            try {
                for (const kind of ['misp', 'attribute', 'object']) {
                    if (!this.icons[kind]) {
                        this.icons[kind] = readIcon('misp-simple misp-icon-' + kind);
                    }
                }
                const catalog = await this.request(this.options.catalogUrl);
                if (this.destroyed) {
                    return;
                }
                this.definitions.forEach(dispose => dispose());
                this.definitions = [];
                const modules = catalog.modules.filter(module => module.available && Object.hasOwn(labels, module.name));
                for (const module of modules) {
                    this.definitions.push(this.graph.pivots.register({id: 'misp:' + module.name, label: module.label && module.label !== module.name ? module.label : labels[module.name], appliesTo: nodes => {
                        const eligible = nodes.filter(node => this.canExpand(node) && inputTypes(node).some(type => module.input_types.includes(type)));
                        return eligible.length === 1 ? eligible : [];
                    }, fetch: (nodes, narrowing, context) => this.expand(nodes[0], module, context)}));
                }
                this.report(modules.length ? 'Select one AIL object, then use Pivot to run a MISP module.' : 'No configured MISP expansion modules are available.');
            } catch (error) {
                if (!this.destroyed && error.name !== 'AbortError') {
                    this.report('MISP expansions unavailable: ' + error.message, 'warning');
                }
            }
        }

        async expand(node, module, context) {
            const signal = context.signal;
            try {
                if (!this.canExpand(node)) {
                    throw new Error('Select an original AIL object to expand.');
                }
                const url = new URL(this.options.modulesUrl, document.baseURI);
                url.searchParams.set('object_id', node.id);
                const discovery = await this.request(url.href, undefined, signal);
                const current = discovery.modules.find(candidate => candidate.name === module.name);
                if (!current?.available || !current.inputs?.length) {
                    throw new Error('This module has no configured compatible input for the selected object. Reload the expansion modules after changing settings.');
                }
                const input = current.inputs.length === 1 ? current.inputs[0] : await this.chooseInput(node, module, current.inputs, signal, context.pivotId);
                if (signal.aborted || context.isStale?.()) {
                    throw new DOMException('Expansion cancelled.', 'AbortError');
                }
                this.report('Running ' + labels[module.name] + '…');
                const response = await this.request(this.options.expandUrl, {object_id: node.id, module: module.name, input_id: input.id}, signal);
                if (signal.aborted || context.isStale?.()) {
                    throw new DOMException('Expansion cancelled.', 'AbortError');
                }
                const graphNodes = new Map(this.graph.getMutableNodes().map(node => [node.id, node]));
                const fragment = conversion.convertResponse(response, {baseNodes: [...graphNodes.values()]});
                for (const descriptor of fragment.nodes) {
                    const attributeType = descriptor.data._misp.attribute_type;
                    const attributeIconName = attributeType?.toLowerCase().replace(/\|/g, '-');
                    if (attributeIconName && /^[a-z0-9][a-z0-9_-]*$/.test(attributeIconName) && !this.icons.attributes.has(attributeType)) {
                        this.icons.attributes.set(attributeType, readIcon('misp-attributes misp-icon-' + attributeIconName));
                    }
                    const objectName = descriptor.data._misp.object_name;
                    if (objectName && /^[a-z0-9][a-z0-9_-]*$/.test(objectName) && !this.icons.objects.has(objectName)) {
                        this.icons.objects.set(objectName, readIcon('misp-objects misp-icon-' + objectName));
                    }
                    const existing = this.graph.getMutableNode(descriptor.id);
                    const knownIdentity = dataOf(existing)._misp?.identity;
                    if (knownIdentity && knownIdentity !== descriptor.identity) {
                        throw new Error('Graph identity collision.');
                    }
                }
                this.report(response.status === 'empty' ? labels[module.name] + ': no results. Existing results remain.' : labels[module.name] + ': results received. Pivotick will add them or open Review.');
                return candidates(fragment, graphNodes, this.icons);
            } catch (error) {
                if (error.name !== 'AbortError') {
                    this.report(labels[module.name] + ': ' + error.message, 'danger');
                }
                throw error;
            }
        }

        chooseInput(node, module, inputs, signal, pivotId) {
            return new Promise((resolve, reject) => {
                const dialog = element('dialog', 'misp-input-dialog');
                const form = element('form');
                const title = element('h4', '', 'Choose an input for ' + labels[module.name]);
                title.id = 'misp-input-title';
                dialog.setAttribute('aria-labelledby', title.id);
                const select = element('select', 'form-control mb-3');
                select.id = 'misp-expansion-input';
                const label = element('label', '', 'Exported observable');
                label.htmlFor = select.id;
                inputs.forEach(input => {
                    const option = element('option', '', input.object_name + ' · ' + (input.object_relation || input.type) + ': ' + input.value);
                    option.value = input.id;
                    select.append(option);
                });
                const actions = element('div', 'd-flex justify-content-end');
                const cancel = element('button', 'btn btn-outline-secondary mr-2', 'Cancel');
                cancel.type = 'button';
                const run = element('button', 'btn btn-primary', 'Run module');
                run.type = 'submit';
                actions.append(cancel, run);
                form.append(title, element('p', 'text-muted', dataOf(node).label || node.id), label, select, actions);
                dialog.append(form);
                document.body.append(dialog);
                const close = () => {
                    signal.removeEventListener('abort', abort);
                    this.abort.signal.removeEventListener('abort', abort);
                    dialog.close();
                    dialog.remove();
                };
                const abort = () => {
                    close();
                    reject(new DOMException('Expansion cancelled.', 'AbortError'));
                };
                const cancelRun = event => {
                    event.preventDefault();
                    this.graph.pivots.cancelFetch(pivotId);
                    if (dialog.isConnected) {
                        abort();
                    }
                };
                signal.addEventListener('abort', abort, {once: true});
                this.abort.signal.addEventListener('abort', abort, {once: true});
                cancel.addEventListener('click', cancelRun);
                dialog.addEventListener('cancel', cancelRun);
                form.addEventListener('submit', event => {
                    event.preventDefault();
                    const input = inputs.find(input => input.id === select.value);
                    close();
                    resolve(input);
                });
                if (signal.aborted || this.abort.signal.aborted) {
                    abort();
                } else {
                    dialog.showModal();
                    select.focus();
                }
            });
        }

        details(element) {
            const live = this.graph.getMutableNode(element.id) || this.graph.getMutableEdge(element.id);
            const ledger = live?.cloneLedger?.() || new Map();
            const contributions = [];
            for (const entry of this.committed) {
                if (ledger.get(entry.pivotId)?.some(claim => claim.runId === entry.runId)) {
                    contributions.push(...(entry.entities.get(element.id) || []));
                }
            }
            return contributions;
        }

        properties(node) {
            const rows = [];
            const seen = new Set();
            for (const contribution of this.details(node)) {
                for (const field of contribution.fields) {
                    const value = Array.isArray(field.value) ? field.value.join('\n') : field.name === 'First seen' || field.name === 'Last seen' ? readableDate(field.value) : field.value;
                    const key = JSON.stringify([field.name, value]);
                    if (!seen.has(key)) {
                        seen.add(key);
                        rows.push({name: field.name, value});
                    }
                }
            }
            return rows;
        }

        renderDetails(node) {
            const wrapper = element('div', 'misp-graph-details');
            const rows = this.properties(node);
            wrapper.append(element('div', 'misp-graph-source', 'MISP Modules'));
            const list = element('dl', 'misp-graph-fields');
            for (const row of rows) {
                list.append(element('dt', '', row.name), element('dd', '', row.value));
            }
            wrapper.append(list);
            return wrapper;
        }

        destroy() {
            this.destroyed = true;
            this.abort.abort();
            this.definitions.forEach(dispose => dispose());
            this.unsubscribe();
            this.unsubscribeHistory?.();
            if (this.graph.pivots.ingest === this.ingest) {
                this.graph.pivots.ingest = this.originalIngest;
            }
            if (this.graph.pivots.mark === this.mark) {
                this.graph.pivots.mark = this.originalMark;
            }
            if (this.graph.pivots.markAll === this.markAll) {
                this.graph.pivots.markAll = this.originalMarkAll;
            }
            if (this.triage && this.triage.toastIngest === this.toastIngest) {
                this.triage.toastIngest = this.originalToastIngest;
            }
            this.pendingMetadata.clear();
            this.committed = [];
        }
    }

    function attach(graph, controls, options = {}) {
        const text = controls.querySelector('[data-misp-status]');
        const reload = controls.querySelector('[data-misp-reload]');
        const controller = new NativePivots(graph, {...options, controls, catalogUrl: controls.dataset.catalogUrl, modulesUrl: controls.dataset.modulesUrl, expandUrl: controls.dataset.expandUrl, onStatus: (message, kind) => {
            text.textContent = message;
            controls.classList.toggle('text-danger', kind === 'danger');
            controls.classList.toggle('text-warning', kind === 'warning');
        }});
        reload.onclick = async () => {
            reload.disabled = true;
            try {
                await controller.load();
            } finally {
                reload.disabled = false;
            }
        };
        reload.onclick();
        return controller;
    }

    return {NativePivots, candidates, inputTypes, readableDate, attach};
});
