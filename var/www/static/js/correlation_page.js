/* Asynchronous exploration, bookmarkable settings and browser history. */
(function () {
    'use strict';

    class CorrelationPage {
        constructor(config, renderGraph) {
            this.config = config;
            this.renderGraph = renderGraph;
            this.form = document.getElementById('correlation-settings');
            this.types = [...this.form.querySelectorAll('[data-correlation-type]')];
            this.depth = document.getElementById('correlation-depth');
            this.limit = document.getElementById('correlation-limit');
            this.customDepth = document.getElementById('correlation-depth-custom');
            this.customLimit = document.getElementById('correlation-limit-custom');
            this.graph = null;
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
                'selection-details': () => this.graph?.UIManager.sidebar?.showSidebar(),
                objects: () => this.graph?.openTable(),
                center: () => {
                    const node = this.graph?.getMutableNode(this.config.object.gid);
                    if (node) {
                        this.graph.focusElement(node);
                    }
                },
                restore: () => {
                    this.navigate({...this.config.state, hidden: []});
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
                if (this.busy || !window.ltags || !window.ltagsgalaxies) {
                    event.preventDefault();
                    document.getElementById('correlation-tags-status').textContent = this.busy ? 'Wait for the graph update before tagging this exploration.' : 'The tag selector is still loading. Please try again in a moment.';
                }
            });
            window.addEventListener('popstate', event => {
                const entry = event.state?.ailCorrelation;
                if (!entry || entry.object !== this.config.object.gid) {
                    window.location.reload();
                    return;
                }
                this.saveView();
                this.setControls(entry.settings);
                this.load({settings: entry.settings, url: window.location.href, history: 'none', entryId: entry.id, view: this.views.get(entry.id)});
            });
            this.syncSettings();
            this.syncScope();
        }

        newEntryId() {
            return Date.now().toString(36) + '-' + Math.random().toString(36).slice(2);
        }

        historyEntry(settings, id) {
            return {...history.state, ailCorrelation: {object: this.config.object.gid, settings, id}};
        }

        setControls(state) {
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

        draft() {
            return {
                types: this.types.filter(input => input.checked).map(input => input.value),
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
            document.getElementById('correlation-types-caption').textContent = draft.types.length + '/' + this.types.length + ' types selected';
            document.getElementById('correlation-apply').disabled = !validTypes;
            this.form.querySelector('[data-correlation-action="direct"]').disabled = !validTypes;
            document.getElementById('correlation-settings-error').hidden = validTypes;
            document.getElementById('correlation-filter').value = draft.types.join(',');
            document.getElementById('correlation-level').value = draft.level;
            document.getElementById('correlation-max-nodes').value = draft.maxNodes;
            const state = this.config.state;
            this.form.querySelector('[data-correlation-action="direct"]').setAttribute('aria-pressed', String(state.level === 0));
            const changed = draft.level !== state.level || draft.maxNodes !== state.maxNodes || [...draft.types].sort().join(',') !== [...state.types].sort().join(',');
            const steps = state.level + 1;
            document.getElementById('correlation-settings-summary').textContent = state.types.length + '/' + this.types.length + ' types · ' + (steps === 1 ? 'Direct correlations' : steps + ' steps from starting object') + ' · Limit ' + state.maxNodes + (changed ? ' · Changes not applied' : '');
            return validTypes;
        }

        urlFor(settings) {
            const url = new URL(window.location.href);
            url.pathname = new URL(this.config.urls.page, window.location.href).pathname;
            url.searchParams.set('type', this.config.object.type);
            url.searchParams.set('subtype', this.config.object.subtype);
            url.searchParams.set('id', this.config.object.id);
            url.searchParams.set('mode', settings.mode || this.config.state.mode);
            url.searchParams.set('filter', settings.types.join(','));
            url.searchParams.set('level', settings.level);
            url.searchParams.set('max_nodes', settings.maxNodes);
            const hidden = settings.hidden || [...(this.liveHidden || this.config.state.hidden)];
            url.searchParams.delete('hide');
            if (hidden.length) {
                url.searchParams.set('hidden', hidden.join(','));
            } else {
                url.searchParams.delete('hidden');
            }
            return url;
        }

        navigate(settings) {
            const state = {...this.config.state, ...settings, hidden: settings.hidden || [...(this.liveHidden || this.config.state.hidden)]};
            this.load({settings: state, url: this.urlFor(state).href, history: 'push'});
        }

        graphUrl(settings) {
            const url = new URL(this.config.urls.graph, window.location.href);
            url.search = this.urlFor(settings).search;
            return url;
        }

        setBusy(busy) {
            this.busy = busy;
            document.getElementById('correlation-request-status').hidden = !busy;
            document.querySelector('.correlation-graph-card').setAttribute('aria-busy', String(busy));
            document.querySelector('#correlation-tags-form button[type="submit"]').disabled = busy;
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
                    throw new Error(response.status === 404 ? 'This object is no longer available.' : 'Unable to load correlations (HTTP ' + response.status + '). Please try again.');
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
                this.config.state = request.settings;
                const graph = this.renderGraph(data, request.view || previous);
                this.attachGraph(graph, data);
                this.rendering = new Promise(resolve => {
                    graph.on('ready', () => {
                        if (graph === this.graph) {
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
                if (request.history === 'push' && request.url !== window.location.href) {
                    this.entryId = this.newEntryId();
                    history.pushState(this.historyEntry(request.settings, this.entryId), '', request.url);
                } else if (request.entryId) {
                    this.entryId = request.entryId;
                } else {
                    this.entryId = history.state?.ailCorrelation?.id || this.entryId;
                    history.replaceState(this.historyEntry(request.settings, this.entryId), '', request.url);
                }
                this.appliedUrl = request.url;
                this.config.urls.graph = this.graphUrl(request.settings).href;
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
                    this.showError(error instanceof SyntaxError ? 'The server returned an invalid graph response. Please try again.' : error.message || 'Unable to load correlations. Please try again.');
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
                throw new Error('The server returned invalid graph correlations. Please try again.');
            }
        }

        syncScope() {
            const state = this.config.state;
            this.form.elements.hidden.value = state.hidden.join(',');
            const form = document.getElementById('correlation-tags-form');
            for (const [name, value] of Object.entries({tag_level: state.level, tag_nb_max: state.maxNodes, tag_filter: state.types.join(','), tag_hidden: state.hidden.join(',')})) {
                form.elements[name].value = value;
            }
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

        hideObjects(nodes) {
            const hidden = new Set(this.liveHidden || this.config.state.hidden);
            const previousSize = hidden.size;
            nodes.forEach(node => {
                if (node.id !== this.config.object.gid && node.getData()._ail) {
                    hidden.add(node.id);
                }
            });
            if (hidden.size !== previousSize) {
                this.navigate({...this.config.state, hidden: [...hidden]});
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
            document.querySelectorAll('[data-correlation-type-icon]').forEach(element => {
                const icons = window.all_graph.legend.entries.get(element.dataset.correlationTypeIcon)?.button.querySelector('.correlation-legend-icons');
                if (icons) {
                    element.replaceChildren(icons.cloneNode(true));
                }
            });
            const interaction = graph.renderer.getGraphInteraction();
            const sync = () => {
                const selected = this.selectedObjects();
                document.getElementById('correlation-selected-count').textContent = selected.length;
                document.querySelector('[data-correlation-action="focus"]').disabled = selected.length === 0;
                const hasSelection = selected.length > 0 || interaction.getSelectedEdges().length > 0;
                for (const action of ['clear', 'selection-details']) {
                    document.querySelector('[data-correlation-action="' + action + '"]').disabled = !hasSelection;
                }
                document.querySelector('[data-correlation-action="hide"]').disabled = !selected.some(node => node.id !== this.config.object.gid && node.getData()._ail);
                const excluded = graph.queryEngine.getFilters().manuallyHidden?.value || [];
                const hidden = new Set([...this.config.state.hidden, ...excluded]);
                document.getElementById('correlation-hidden-count').textContent = hidden.size;
                document.querySelector('[data-correlation-action="restore"]').disabled = hidden.size === 0;
                document.getElementById('correlation-loaded-count').textContent = graph.getMutableNodes().filter(node => node.visible).length;
                document.getElementById('correlation-group-count').textContent = graph.simplify.getGroups().filter(group => !group.open).length;
                this.liveHidden = hidden;
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
