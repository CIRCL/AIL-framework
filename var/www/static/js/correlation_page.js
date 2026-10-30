/* Shared correlation and relationship exploration, settings and browser history. */
(function () {
    'use strict';

    class CorrelationPage {
        constructor(config, renderGraph) {
            this.config = config;
            this.renderGraph = renderGraph;
            this.form = document.getElementById('correlation-settings');
            this.types = [...this.form.querySelectorAll('[data-correlation-type]')];
            this.relationships = [...this.form.querySelectorAll('[data-relationship-type]')];
            this.relationshipView = config.kind === 'relationship';
            this.linkName = this.relationshipView ? 'relationships' : 'correlations';
            this.depth = document.getElementById('correlation-depth');
            this.limit = document.getElementById('correlation-limit');
            this.customDepth = document.getElementById('correlation-depth-custom');
            this.customLimit = document.getElementById('correlation-limit-custom');
            this.graph = null;
            this.graphReady = false;
            this.visibilityDepth = 0;
            this.visibilityTicket = null;
            this.hideBatches = [];
            this.config.state.hidden = this.hiddenIds(this.config.state.hidden);
            this.busy = false;
            this.rendering = Promise.resolve();
            this.requestNumber = 0;
            this.draftRevision = 0;
            this.views = new Map();
            this.entryId = this.newEntryId();
            this.appliedUrl = this.urlFor(config.state).href;
            history.replaceState(this.historyEntry(config.state, this.entryId), '', this.appliedUrl);
            this.actions = {
                'types-all': () => this.selectTypes(true),
                'types-clear': () => this.selectTypes(false),
                'relationships-all': () => this.selectRelationships(true),
                'relationships-clear': () => this.selectRelationships(false),
                direct: () => {
                    this.depth.value = '0';
                    this.syncSettings();
                    this.form.requestSubmit();
                },
                reset: () => {
                    this.setControls(this.config.defaults);
                    this.navigate(this.config.defaults);
                },
                retry: () => {
                    if (this.failedRequest) {
                        this.load(this.failedRequest);
                    }
                },
                cancel: () => this.request?.abort(),
                'object-details': () => {
                    const details = document.getElementById('correlation-object-details');
                    details.open = true;
                    details.querySelector('summary').focus();
                    details.scrollIntoView({block: 'nearest', behavior: 'smooth'});
                },
                clear: () => this.graph?.selectElements([]),
                focus: () => this.focusSelection(),
                hide: () => this.hideObjects(this.selectedObjects()),
                'undo-hide': () => this.undoLastHide(),
                'selection-details': () => this.graph?.UIManager.sidebar?.showSidebar(),
                objects: () => this.graph?.openTable(),
                center: () => {
                    const node = this.graph?.getMutableNode(this.config.object.gid);
                    if (node) {
                        this.graph.focusElement(node);
                    }
                },
                restore: () => {
                    this.changeHidden([]);
                },
                'increase-limit': () => {
                    this.limit.focus();
                    this.form.scrollIntoView({block: 'nearest', behavior: 'smooth'});
                },
            };
            document.addEventListener('click', event => {
                const action = event.target.closest('[data-correlation-action]');
                if (action && !action.disabled) {
                    this.actions[action.dataset.correlationAction]?.();
                }
                document.querySelectorAll('[data-correlation-popover][open]').forEach(details => {
                    if (!details.contains(event.target)) {
                        details.open = false;
                    }
                });
            });
            document.addEventListener('keydown', event => {
                if (event.key === 'Escape') {
                    document.querySelectorAll('[data-correlation-popover][open]').forEach(details => {
                        details.open = false;
                        details.querySelector('summary').focus();
                    });
                }
            });
            document.getElementById('correlation-type-picker').addEventListener('toggle', event => {
                if (event.target.open) {
                    document.getElementById('correlation-type-search').focus();
                }
            });
            document.getElementById('correlation-type-search').addEventListener('input', event => {
                const query = event.target.value.trim().toLowerCase();
                const options = [...this.form.querySelectorAll('[data-type-label]')];
                options.forEach(option => {
                    option.hidden = !option.dataset.typeLabel.includes(query);
                });
                document.getElementById('correlation-type-empty').hidden = options.some(option => !option.hidden);
            });
            document.getElementById('correlation-type-search').addEventListener('keydown', event => {
                if (event.key === 'Enter') {
                    event.preventDefault();
                }
            });
            for (const name of ['input', 'change']) {
                this.form.addEventListener(name, () => {
                    this.draftRevision++;
                    this.syncSettings();
                });
            }
            this.form.addEventListener('submit', event => {
                event.preventDefault();
                if (this.syncSettings() && this.form.reportValidity()) {
                    this.navigate(this.draft());
                }
            });
            document.getElementById('correlation-tags-form').addEventListener('submit', event => {
                this.syncScope();
                if (this.busy || !this.graphReady || !this.visibleObjects().length || !window.ltags || !window.ltagsgalaxies) {
                    event.preventDefault();
                    document.getElementById('correlation-tags-status').textContent = this.busy || !this.graphReady ? 'Wait for the graph update before tagging this exploration.' : !this.visibleObjects().length ? 'There are no visible AIL objects to tag.' : 'The tag selector is still loading. Please try again in a moment.';
                }
            });
            window.addEventListener('popstate', event => {
                const entry = event.state?.ailCorrelation;
                if (!entry || entry.object !== this.config.object.gid || entry.kind !== this.config.kind) {
                    window.location.reload();
                    return;
                }
                this.saveView();
                this.setControls(entry.settings);
                const request = {settings: entry.settings, url: window.location.href, history: 'none', entryId: entry.id, view: this.views.get(entry.id)};
                if (this.graphReady && this.datasetKey(entry.settings) === this.datasetKey(this.config.state)) {
                    this.changeHidden(entry.settings.hidden, request);
                    this.restoreView(request.view, null);
                } else {
                    this.load(request);
                }
            });
            this.syncSettings();
            this.syncScope();
        }

        newEntryId() {
            return Date.now().toString(36) + '-' + Math.random().toString(36).slice(2);
        }

        historyEntry(settings, id) {
            return {...history.state, ailCorrelation: {object: this.config.object.gid, kind: this.config.kind, settings, id}};
        }

        hiddenIds(ids) {
            return [...new Set(ids)].filter(id => typeof id === 'string' && id && id !== this.config.object.gid).sort();
        }

        datasetKey(state) {
            return JSON.stringify([[...state.types].sort(), state.level, state.maxNodes, state.mode, [...(state.relationships || [])].sort()]);
        }

        setControls(state) {
            this.relationships.forEach(input => {
                input.checked = state.relationships.includes(input.value);
            });
            this.types.forEach(input => {
                input.checked = state.types.includes(input.value);
            });
            this.depth.value = [0, 1, 2].includes(state.level) ? String(state.level) : 'custom';
            this.customDepth.value = state.level + 1;
            this.limit.value = [100, 300, 500, 1000, 10000].includes(state.maxNodes) ? String(state.maxNodes) : 'custom';
            this.customLimit.value = state.maxNodes;
            this.draftRevision++;
            this.syncSettings();
        }

        selectTypes(checked) {
            this.types.forEach(input => {
                input.checked = checked;
            });
            this.draftRevision++;
            this.syncSettings();
        }

        selectRelationships(checked) {
            this.relationships.forEach(input => {
                input.checked = checked;
            });
            this.draftRevision++;
            this.syncSettings();
        }

        draft() {
            return {
                types: this.types.filter(input => input.checked).map(input => input.value),
                relationships: this.relationships.filter(input => input.checked).map(input => input.value),
                level: this.depth.value === 'custom' ? Number(this.customDepth.value) - 1 : Number(this.depth.value),
                maxNodes: this.limit.value === 'custom' ? Number(this.customLimit.value) : Number(this.limit.value),
            };
        }

        syncSettings() {
            const customDepth = this.depth.value === 'custom';
            const customLimit = this.limit.value === 'custom';
            document.getElementById('correlation-depth-custom-field').hidden = !customDepth;
            document.getElementById('correlation-limit-custom-field').hidden = !customLimit;
            this.customDepth.disabled = !customDepth;
            this.customDepth.required = customDepth;
            this.customLimit.disabled = !customLimit;
            this.customLimit.required = customLimit;
            const draft = this.draft();
            const validTypes = draft.types.length > 0;
            const valid = validTypes && (!this.relationshipView || draft.relationships.length > 0);
            document.getElementById('correlation-types-caption').textContent = draft.types.length + '/' + this.types.length + ' types selected';
            document.getElementById('correlation-apply').disabled = !valid;
            this.form.querySelector('[data-correlation-action="direct"]').disabled = !valid;
            const error = document.getElementById('correlation-settings-error');
            error.hidden = valid;
            error.textContent = validTypes ? 'Select at least one relationship.' : 'Select at least one object type.';
            if (this.relationshipView) {
                document.getElementById('relationship-types-caption').textContent = draft.relationships.length + '/' + this.relationships.length + ' relationships';
                document.getElementById('relationship-filter').value = draft.relationships.join(',');
            }
            document.getElementById('correlation-filter').value = draft.types.join(',');
            document.getElementById('correlation-level').value = draft.level;
            document.getElementById('correlation-max-nodes').value = draft.maxNodes;
            const state = this.config.state;
            this.form.querySelector('[data-correlation-action="direct"]').setAttribute('aria-pressed', String(state.level === 0));
            const changed = draft.level !== state.level || draft.maxNodes !== state.maxNodes || [...draft.types].sort().join(',') !== [...state.types].sort().join(',') || this.relationshipView && [...draft.relationships].sort().join(',') !== [...state.relationships].sort().join(',');
            const steps = state.level + 1;
            const relationships = this.relationshipView ? ' · ' + state.relationships.length + '/' + this.relationships.length + ' relationships' : '';
            document.getElementById('correlation-settings-summary').textContent = state.types.length + '/' + this.types.length + ' types' + relationships + ' · ' + (steps === 1 ? 'Direct ' + this.linkName : steps + ' steps from starting object') + ' · Limit ' + state.maxNodes + (changed ? ' · Changes not applied' : '');
            return valid;
        }

        urlFor(settings) {
            const url = new URL(window.location.href);
            url.pathname = new URL(this.config.urls.page, window.location.href).pathname;
            url.searchParams.set('type', this.config.object.type);
            url.searchParams.set('subtype', this.config.object.subtype);
            url.searchParams.set('id', this.config.object.id);
            if (this.relationshipView) {
                url.searchParams.delete('mode');
                url.searchParams.set('relationships', settings.relationships.join(','));
            } else {
                url.searchParams.set('mode', settings.mode || this.config.state.mode);
            }
            url.searchParams.set('filter', settings.types.join(','));
            url.searchParams.set('level', settings.level);
            url.searchParams.set('max_nodes', settings.maxNodes);
            const hidden = settings.hidden || this.config.state.hidden;
            url.searchParams.delete('hide');
            if (hidden.length) {
                url.searchParams.set('hidden', hidden.join(','));
            } else {
                url.searchParams.delete('hidden');
            }
            return url;
        }

        navigate(settings) {
            const state = {...this.config.state, ...settings, hidden: this.hiddenIds(settings.hidden || this.currentHidden())};
            this.load({settings: state, url: this.urlFor(state).href, history: 'push'});
        }

        graphUrl(settings) {
            const url = new URL(this.config.urls.graph, window.location.href);
            url.search = this.urlFor(settings).search;
            url.searchParams.delete('hidden');
            url.searchParams.delete('hide');
            return url;
        }

        setBusy(busy) {
            this.busy = busy;
            document.getElementById('correlation-request-status').hidden = !busy;
            document.querySelector('.correlation-graph-card').setAttribute('aria-busy', String(busy));
            this.syncScope();
            if (!busy) {
                document.getElementById('graph_loading').hidden = true;
            }
        }

        async load(request) {
            this.request?.abort();
            const abort = this.request = new AbortController();
            const number = ++this.requestNumber;
            const revision = this.draftRevision;
            this.failedRequest = null;
            document.getElementById('correlation-graph-error').hidden = true;
            document.querySelector('[data-correlation-action="cancel"]').hidden = !this.graph;
            document.getElementById('correlation-request-message').textContent = this.graph ? 'Updating graph…' : 'Loading graph…';
            this.setBusy(true);
            try {
                const response = await fetch(this.graphUrl(request.settings), {signal: abort.signal, credentials: 'same-origin', cache: 'no-store', headers: {'Accept': 'application/json'}});
                if (response.status === 401 || response.status === 403 || response.redirected) {
                    throw new Error('Unable to read the graph response. Reload the page to check your session.');
                }
                if (!response.ok) {
                    throw new Error(response.status === 404 ? 'This object is no longer available.' : 'Unable to load ' + this.linkName + ' (HTTP ' + response.status + '). Please try again.');
                }
                if (!response.headers.get('Content-Type')?.includes('application/json')) {
                    throw new Error('Unable to read the graph response. Reload the page to check your session.');
                }
                const data = await response.json();
                this.validateData(data);
                // A native graph must finish mounting before its listeners and renderer are destroyed.
                await this.rendering;
                if (abort.signal.aborted || number !== this.requestNumber) {
                    return;
                }
                this.saveView();
                const previous = this.captureView();
                this.detachGraph();
                this.config.state = {...request.settings, hidden: this.hiddenIds(request.settings.hidden)};
                this.hideBatches = (request.view || previous)?.hideBatches?.map(batch => [...batch]) || [];
                this.pruneHideBatches(this.config.state.hidden);
                const graph = this.renderGraph(data, request.view || previous);
                this.attachGraph(graph, data);
                this.rendering = new Promise(resolve => {
                    graph.on('ready', () => {
                        if (graph === this.graph) {
                            this.graphReady = true;
                            this.restoreView(request.view, previous);
                            document.querySelector('.correlation-canvas-wrap').classList.remove('is-rendering');
                            this.syncGraph();
                        }
                        resolve();
                    });
                });
                document.querySelector('.correlation-canvas-wrap').classList.add('is-rendering');
                document.querySelector('[data-correlation-action="cancel"]').hidden = true;
                document.getElementById('correlation-request-message').textContent = 'Preparing graph…';
                this.commitLocation(request);
                if (revision === this.draftRevision) {
                    this.setControls(request.settings);
                } else {
                    this.syncSettings();
                }
                this.syncScope();
                await this.rendering;
            } catch (error) {
                if (!abort.signal.aborted && number === this.requestNumber) {
                    this.failedRequest = request;
                    this.showError(error instanceof SyntaxError ? 'The server returned an invalid graph response. Please try again.' : error.message || 'Unable to load ' + this.linkName + '. Please try again.');
                }
            } finally {
                if (number === this.requestNumber) {
                    await this.rendering;
                    if (number === this.requestNumber) {
                        this.setBusy(false);
                    }
                }
            }
        }

        validateData(data) {
            if (!Array.isArray(data?.nodes) || !Array.isArray(data.links) || typeof data.meta?.complete !== 'boolean') {
                throw new Error('The server returned an invalid graph response. Please try again.');
            }
            const ids = new Set();
            for (const node of data.nodes) {
                if (typeof node?.id !== 'string' || !node.style || ids.has(node.id)) {
                    throw new Error('The server returned invalid graph objects. Please try again.');
                }
                ids.add(node.id);
            }
            if (!ids.has(this.config.object.gid) || data.links.some(edge => !edge || !ids.has(edge.source?.id || edge.source) || !ids.has(edge.target?.id || edge.target))) {
                throw new Error('The server returned invalid graph ' + this.linkName + '. Please try again.');
            }
        }

        syncScope() {
            const state = this.config.state;
            this.form.elements.hidden.value = state.hidden.join(',');
            const form = document.getElementById('correlation-tags-form');
            if (this.relationshipView) {
                form.elements.tag_relationships.value = state.relationships.join(',');
            }
            for (const [name, value] of Object.entries({tag_level: state.level, tag_nb_max: state.maxNodes, tag_filter: state.types.join(','), tag_hidden: state.hidden.join(',')})) {
                form.elements[name].value = value;
            }
            const objects = this.visibleObjects().map(node => node.id);
            form.elements.tag_objects.value = JSON.stringify(objects);
            document.getElementById('correlation-tag-count').textContent = objects.length;
            form.querySelector('button[type="submit"]').disabled = this.busy || !this.graphReady || !objects.length;
            document.getElementById('correlation-tags-status').textContent = '';
            document.getElementById('correlation-reload').href = this.appliedUrl;
        }

        groupKey(group) {
            return JSON.stringify(group.members.map(node => node.id).sort());
        }

        captureView() {
            if (!this.graph) {
                return null;
            }
            const graph = this.graph;
            const renderer = graph.renderer;
            const canvas = renderer.getCanvasSelection().node().getBoundingClientRect();
            const transform = renderer.getZoomTransform();
            return {
                selected: this.selectedObjects().map(node => node.id),
                hideBatches: this.hideBatches.map(batch => [...batch]),
                rules: graph.simplify.getRules().map(rule => ({id: rule.id, enabled: rule.enabled, minSize: rule.minSize})),
                open: graph.simplify.getGroups().filter(group => group.open).map(group => this.groupKey(group)),
                positions: graph.getCanvasNodes().filter(node => Number.isFinite(node.x) && Number.isFinite(node.y)).map(node => [node.isGroup ? 'group:' + this.groupKey(node.info) : node.id, node.x, node.y, node.fx, node.fy]),
                viewport: {x: (canvas.width / 2 - transform.x) / transform.k, y: (canvas.height / 2 - transform.y) / transform.k, scale: transform.k},
            };
        }

        saveView() {
            const view = this.captureView();
            if (view) {
                this.views.delete(this.entryId);
                this.views.set(this.entryId, view);
                if (this.views.size > 20) {
                    this.views.delete(this.views.keys().next().value);
                }
            }
        }

        restoreView(view, previous) {
            const graph = this.graph;
            if (view) {
                for (const rule of view.rules) {
                    graph.simplify.setRuleEnabled(rule.id, rule.enabled);
                    graph.simplify.setRuleMinSize(rule.id, rule.minSize);
                }
                const open = new Set(view.open);
                graph.simplify.getGroups().forEach(group => {
                    if (open.has(this.groupKey(group)) && !group.open) {
                        graph.simplify.open(group.id);
                    } else if (!open.has(this.groupKey(group)) && group.open) {
                        graph.simplify.close(group.id);
                    }
                });
            }
            const selected = (view || previous)?.selected || [];
            graph.selectElements(selected.map(id => graph.getMutableNode(id)).filter(node => node?.visible));
            if (view) {
                const positions = new Map(view.positions.map(([id, ...position]) => [id, position]));
                const nodes = graph.getCanvasNodes();
                if (nodes.length === positions.size && nodes.every(node => positions.has(node.isGroup ? 'group:' + this.groupKey(node.info) : node.id))) {
                    nodes.forEach(node => {
                        [node.x, node.y, node.fx, node.fy] = positions.get(node.isGroup ? 'group:' + this.groupKey(node.info) : node.id);
                    });
                    graph.nextTick();
                    graph.renderer.setViewport({...view.viewport, animate: false});
                }
            }
        }

        detachGraph() {
            this.graphCleanup?.();
            this.graph = null;
            this.graphReady = false;
            this.visibilityTicket = null;
        }

        selectedObjects() {
            const nodes = new Map();
            const collect = node => {
                if (node.isGroup) {
                    node.info.members.forEach(collect);
                } else {
                    nodes.set(node.id, node);
                }
            };
            this.graph?.renderer.getGraphInteraction().getSelectedNodes().forEach(({node}) => collect(node));
            return [...nodes.values()];
        }

        visibleObjects() {
            return this.graph?.getMutableNodes().filter(node => node.visible && node.getData()._ail) || [];
        }

        currentHidden(clearMissing = false) {
            if (!this.graph) {
                return this.config.state.hidden;
            }
            const loaded = new Set(this.graph.getMutableNodes().map(node => node.id));
            const missing = clearMissing ? [] : this.config.state.hidden.filter(id => !loaded.has(id));
            return this.hiddenIds([...missing, ...this.graph.queryEngine.getExcludedNodeIds()]);
        }

        commitLocation(request) {
            const state = this.config.state;
            if (request.history === 'push' && request.url !== window.location.href) {
                this.entryId = this.newEntryId();
                history.pushState(this.historyEntry(state, this.entryId), '', request.url);
            } else if (request.entryId) {
                this.entryId = request.entryId;
            } else {
                this.entryId = history.state?.ailCorrelation?.id || this.entryId;
                history.replaceState(this.historyEntry(state, this.entryId), '', request.url);
            }
            this.appliedUrl = request.url;
            this.config.urls.graph = this.graphUrl(state).href;
        }

        cancelForVisibilityChange() {
            if (this.busy) {
                this.request?.abort();
                this.requestNumber++;
                this.setBusy(false);
            }
            this.failedRequest = null;
            document.getElementById('correlation-graph-error').hidden = true;
        }

        pruneHideBatches(hidden) {
            const ids = new Set(hidden);
            this.hideBatches = this.hideBatches.map(batch => batch.filter(id => ids.has(id))).filter(batch => batch.length);
        }

        rememberHide(before, after) {
            this.pruneHideBatches(after);
            const wasHidden = new Set(before);
            const added = after.filter(id => !wasHidden.has(id));
            if (added.length) {
                this.hideBatches.push(added);
                this.hideBatches = this.hideBatches.slice(-30);
            }
        }

        applyHiddenToGraph(hidden) {
            const graph = this.graph;
            const target = new Set(hidden);
            const excluded = new Set(graph.queryEngine.getExcludedNodeIds());
            this.visibilityDepth++;
            try {
                graph.batchChanges(() => graph.history.group(() => {
                    if (!target.size) {
                        graph.queryEngine.clearNodeExclusions();
                        return;
                    }
                    excluded.forEach(id => {
                        if (!target.has(id)) {
                            graph.queryEngine.includeNode(id);
                        }
                    });
                    target.forEach(id => {
                        if (!excluded.has(id)) {
                            graph.queryEngine.excludeNode(id);
                        }
                    });
                }));
            } finally {
                this.visibilityDepth--;
            }
        }

        changeHidden(hidden, request = null) {
            if (!this.graphReady) {
                return;
            }
            this.cancelForVisibilityChange();
            if (!this.visibilityTicket) {
                this.saveView();
            }
            this.visibilityTicket = null;
            const before = this.config.state.hidden;
            const after = this.hiddenIds(hidden);
            this.applyHiddenToGraph(after);
            this.config.state = {...(request?.settings || this.config.state), hidden: after};
            if (request) {
                this.hideBatches = request.view?.hideBatches?.map(batch => [...batch]) || this.hideBatches;
                this.pruneHideBatches(after);
            } else {
                this.rememberHide(before, after);
            }
            this.removeHiddenSelection();
            this.commitLocation(request || {history: 'push', url: this.urlFor(this.config.state).href});
            this.syncGraph();
        }

        scheduleVisibilityChange(graph, clearMissing = false) {
            if (this.visibilityDepth || !this.graphReady || graph !== this.graph) {
                return;
            }
            if (this.visibilityTicket) {
                this.visibilityTicket.clearMissing ||= clearMissing;
                return;
            }
            this.cancelForVisibilityChange();
            this.saveView();
            const ticket = this.visibilityTicket = {graph, clearMissing};
            queueMicrotask(() => {
                if (this.visibilityTicket !== ticket || graph !== this.graph) {
                    return;
                }
                this.visibilityTicket = null;
                const hidden = this.currentHidden(ticket.clearMissing);
                if (hidden.join('\n') !== this.config.state.hidden.join('\n')) {
                    this.rememberHide(this.config.state.hidden, hidden);
                    this.config.state = {...this.config.state, hidden};
                    this.removeHiddenSelection();
                    this.commitLocation({history: 'push', url: this.urlFor(this.config.state).href});
                }
                this.syncGraph();
            });
        }

        removeHiddenSelection() {
            const graph = this.graph;
            const nodes = this.selectedObjects();
            const edges = graph.renderer.getGraphInteraction().getSelectedEdges().map(selection => selection.edge || selection);
            if (nodes.some(node => !node.visible) || edges.some(edge => !edge.visible)) {
                graph.selectElements([...nodes.filter(node => node.visible), ...edges.filter(edge => edge.visible)]);
            }
        }

        hideObjects(nodes) {
            const hidden = new Set(this.currentHidden());
            const collect = node => {
                if (node.isGroup) {
                    node.info.members.forEach(collect);
                } else if (node.id !== this.config.object.gid) {
                    hidden.add(node.id);
                }
            };
            nodes.forEach(collect);
            if (hidden.size !== this.currentHidden().length) {
                this.changeHidden([...hidden]);
            }
        }

        undoLastHide() {
            const batch = this.hideBatches.at(-1);
            if (batch) {
                const latest = this.graph.history.entries()[0];
                if (latest?.kind === 'visibility' && latest.act === 'hide' && [...latest.nodeIds].sort().join('\n') === [...batch].sort().join('\n')) {
                    this.graph.history.undo();
                    return;
                }
                const undo = new Set(batch);
                this.changeHidden(this.currentHidden().filter(id => !undo.has(id)));
            }
        }

        focusSelection() {
            if (!this.graph) {
                return;
            }
            const drawn = [...new Set(this.selectedObjects().map(node => node.canvasRepresentative()))];
            if (!drawn.length) {
                return;
            }
            const left = Math.min(...drawn.map(node => node.x - node.getCircleRadius()));
            const right = Math.max(...drawn.map(node => node.x + node.getCircleRadius()));
            const top = Math.min(...drawn.map(node => node.y - node.getCircleRadius()));
            const bottom = Math.max(...drawn.map(node => node.y + node.getCircleRadius()));
            const box = this.graph.renderer.getCanvasSelection().node().getBoundingClientRect();
            const current = this.graph.renderer.getZoomTransform().k;
            this.graph.renderer.setViewport({x: (left + right) / 2, y: (top + bottom) / 2, scale: Math.min(current, box.width * .8 / Math.max(1, right - left), box.height * .8 / Math.max(1, bottom - top)), animate: true});
        }

        attachGraph(graph, data) {
            this.graph = graph;
            const query = graph.queryEngine;
            const originalExclude = query.excludeNode;
            const originalInclude = query.includeNode;
            const originalClear = query.clearNodeExclusions;
            query.excludeNode = nodeOrId => {
                const node = graph.getMutableNode(nodeOrId);
                if (!node || node.id === this.config.object.gid || (!this.graphReady && !this.visibilityDepth)) {
                    return;
                }
                if (!query.getExcludedNodeIds().includes(node.id)) {
                    graph.UIManager.tooltip?.hide();
                    this.scheduleVisibilityChange(graph);
                }
                return originalExclude.call(query, node);
            };
            query.includeNode = nodeOrId => {
                if (query.getExcludedNodeIds().includes(typeof nodeOrId === 'string' ? nodeOrId : nodeOrId.id)) {
                    this.scheduleVisibilityChange(graph);
                }
                return originalInclude.call(query, nodeOrId);
            };
            query.clearNodeExclusions = () => {
                this.scheduleVisibilityChange(graph, true);
                graph.batchChanges(() => graph.history.group(() => {
                    query.getExcludedNodeIds().forEach(id => query.includeNode(id));
                    originalClear.call(query);
                }));
            };
            this.applyHiddenToGraph(this.config.state.hidden);
            graph.history.clear();
            document.querySelectorAll('[data-correlation-type-icon]').forEach(element => {
                const icons = window.all_graph.legend.entries.get(element.dataset.correlationTypeIcon)?.button.querySelector('.correlation-legend-icons');
                if (icons) {
                    element.replaceChildren(icons.cloneNode(true));
                }
            });
            const interaction = graph.renderer.getGraphInteraction();
            const sync = () => {
                if (this.visibilityDepth) {
                    return;
                }
                const selected = this.selectedObjects();
                document.getElementById('correlation-selected-count').textContent = selected.length;
                document.querySelector('[data-correlation-action="focus"]').disabled = selected.length === 0;
                const hasSelection = selected.length > 0 || interaction.getSelectedEdges().length > 0;
                for (const action of ['clear', 'selection-details']) {
                    document.querySelector('[data-correlation-action="' + action + '"]').disabled = !hasSelection;
                }
                document.querySelector('[data-correlation-action="hide"]').disabled = !this.graphReady || !selected.some(node => node.id !== this.config.object.gid && node.visible);
                const nodes = graph.getMutableNodes();
                const excluded = new Set(query.getExcludedNodeIds());
                const hidden = nodes.filter(node => excluded.has(node.id)).length;
                document.getElementById('correlation-hidden-count').textContent = hidden;
                document.getElementById('correlation-hidden-count').title = this.config.state.hidden.length + ' hidden objects remembered, including objects outside the current loaded graph.';
                document.querySelector('[data-correlation-action="restore"]').disabled = !this.graphReady || !this.config.state.hidden.length;
                document.querySelector('[data-correlation-action="undo-hide"]').disabled = !this.graphReady || !this.hideBatches.length;
                document.getElementById('correlation-loaded-count').textContent = nodes.length;
                document.getElementById('correlation-visible-count').textContent = nodes.filter(node => node.visible).length;
                document.getElementById('correlation-group-count').textContent = graph.simplify.getGroups().filter(group => !group.open).length;
                document.getElementById('correlation-empty').hidden = graph.getMutableEdges().some(edge => edge.visible);
                this.syncScope();
            };
            this.syncGraph = sync;
            for (const name of ['selectNode', 'unselectNode', 'selectNodes', 'unselectNodes', 'selectEdges', 'unselectEdges']) {
                interaction.on(name, sync);
            }
            graph.queryEngine.on('filterChange', sync);
            const unsubscribeGroups = graph.simplify.onChange(sync);
            graph.on('dataBatchChanged', sync);
            this.graphCleanup = () => {
                for (const name of ['selectNode', 'unselectNode', 'selectNodes', 'unselectNodes', 'selectEdges', 'unselectEdges']) {
                    interaction.off(name, sync);
                }
                graph.queryEngine.off('filterChange', sync);
                graph.off('dataBatchChanged', sync);
                unsubscribeGroups();
                query.excludeNode = originalExclude;
                query.includeNode = originalInclude;
                query.clearNodeExclusions = originalClear;
            };
            document.getElementById('incomplete_graph').hidden = data.meta.complete;
            document.getElementById('correlation-empty').hidden = data.links.length > 0;
            for (const action of ['center', 'objects']) {
                document.querySelector('[data-correlation-action="' + action + '"]').disabled = false;
            }
            sync();
        }

        showError(message) {
            document.getElementById('graph_loading').hidden = true;
            const error = document.getElementById('correlation-graph-error');
            document.getElementById('correlation-graph-error-message').textContent = message + (this.graph ? ' The previous graph is still shown.' : '');
            error.hidden = false;
        }
    }

    window.AILCorrelationPage = {
        attach: function(config, renderGraph) {
            return new CorrelationPage(config, renderGraph);
        },
    };
})();
