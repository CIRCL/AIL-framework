(function (host, factory) {
    'use strict';
    const api = factory();
    if (typeof module === 'object' && module.exports) {
        module.exports = api;
    }
    if (host) {
        host.AILModulesGraph = api;
    }
})(typeof window === 'undefined' ? null : window, function () {
    'use strict';

    const COLORS = {registered: '#2563eb', waiting: '#b45309', unknown: '#64748b'};

    function renderModule(node) {
        const card = document.createElement('div');
        card.className = 'modules-graph-module';
        card.style.setProperty('--module-accent', node.getStyle().color);
        const label = document.createElement('span');
        label.className = 'modules-graph-module-label';
        const parts = node.getData().label.split(/(?<=[a-z0-9])(?=[A-Z])|(?<=_)/);
        parts.forEach((part, index) => {
            if (index) {
                label.appendChild(document.createElement('wbr'));
            }
            label.appendChild(document.createTextNode(part));
        });
        card.appendChild(label);
        return card;
    }

    function moduleLevels(nodes, edges) {
        const outgoing = new Map(nodes.map(node => [node.id, []]));
        edges.forEach(edge => outgoing.get(edge.source).push(edge.target));
        const indices = new Map();
        const lowest = new Map();
        const stack = [];
        const active = new Set();
        const component = new Map();
        let componentCount = 0;

        // Keep cycles in one layer, then order the resulting acyclic graph.
        function visit(id) {
            indices.set(id, indices.size);
            lowest.set(id, indices.get(id));
            stack.push(id);
            active.add(id);
            for (const target of outgoing.get(id)) {
                if (!indices.has(target)) {
                    visit(target);
                    lowest.set(id, Math.min(lowest.get(id), lowest.get(target)));
                } else if (active.has(target)) {
                    lowest.set(id, Math.min(lowest.get(id), indices.get(target)));
                }
            }
            if (lowest.get(id) === indices.get(id)) {
                let member;
                do {
                    member = stack.pop();
                    active.delete(member);
                    component.set(member, componentCount);
                } while (member !== id);
                componentCount++;
            }
        }
        nodes.forEach(node => {
            if (!indices.has(node.id)) {
                visit(node.id);
            }
        });
        const parents = Array.from({length: componentCount}, () => new Set());
        edges.forEach(edge => {
            const source = component.get(edge.source);
            const target = component.get(edge.target);
            if (source !== target) {
                parents[target].add(source);
            }
        });
        const levels = new Map();
        function level(id) {
            if (!levels.has(id)) {
                levels.set(id, Math.max(0, ...[...parents[id]].map(parent => level(parent) + 1)));
            }
            return levels.get(id);
        }
        return new Map(nodes.map(node => [node.id, level(component.get(node.id))]));
    }

    function buildData(topology, stats) {
        if (topology.version !== 1 || !Array.isArray(topology.nodes) || !Array.isArray(topology.edges)) {
            throw new Error('Unsupported module graph format.');
        }
        const definitions = new Map(topology.nodes.map(node => [node.id, node]));
        // Retain runtime-only modules without inventing configured routes for them.
        for (const name of Object.keys(stats)) {
            if (!definitions.has(name)) {
                definitions.set(name, {id: name, subscribe: null, publish: [], runtimeOnly: true});
            }
        }
        const nodes = [...definitions.values()].map(node => {
            const snapshot = stats[node.id];
            const workers = snapshot ? Object.values(snapshot.modules || {}) : null;
            const pending = snapshot && snapshot.in !== null && snapshot.in !== undefined && Number.isFinite(Number(snapshot.in)) ? Number(snapshot.in) : null;
            const registered = workers === null ? null : workers.length;
            const status = pending > 0 && registered === 0 ? 'waiting' : registered > 0 ? 'registered' : 'unknown';
            return {
                id: node.id,
                data: {
                    label: node.id,
                    description: snapshot ? `${registered} registered workers · ${pending === null ? 'unknown' : pending.toLocaleString()} pending messages` : 'No runtime statistics',
                    subscribe: node.subscribe,
                    publish: node.publish,
                    runtimeOnly: Boolean(node.runtimeOnly),
                    registered,
                    pending,
                    workers,
                    status,
                },
                style: {color: COLORS[status], shape: 'none'},
            };
        });
        const edges = topology.edges.map(edge => {
            if (!definitions.has(edge.source) || !definitions.has(edge.target)) {
                throw new Error('A module connection has an unknown endpoint.');
            }
            return {
                id: JSON.stringify([edge.source, edge.channel, edge.target]),
                source: edge.source,
                target: edge.target,
                data: {label: edge.channel, description: `${edge.source} → ${edge.target}`, source: edge.source, target: edge.target},
            };
        });
        const levels = moduleLevels(nodes, edges);
        nodes.forEach(node => {
            node.data.level = levels.get(node.id);
        });
        return {nodes, edges};
    }

    function readableTime(value) {
        const seconds = Number(value);
        const date = new Date(seconds * 1000);
        if (!Number.isFinite(seconds) || seconds <= 0 || !Number.isFinite(date.getTime())) {
            return 'Unknown';
        }
        return date.toLocaleString();
    }

    function properties(element) {
        const data = element.getData();
        if (data.source !== undefined) {
            return [
                {name: 'Routing channel', value: data.label},
                {name: 'From module', value: data.source},
                {name: 'To module', value: data.target},
            ];
        }
        const fields = [
            {name: 'Subscribed channel', value: data.subscribe || 'None'},
            {name: 'Published channels', value: data.publish.length ? data.publish.join(', ') : 'None'},
            {name: 'Registered workers', value: data.registered === null ? 'Unknown' : String(data.registered)},
            {name: 'Pending messages', value: data.pending === null ? 'Unknown' : data.pending.toLocaleString()},
        ];
        for (const [index, worker] of (data.workers || []).entries()) {
            fields.push({name: `Worker ${index + 1} · started`, value: readableTime(worker.start)});
            fields.push({name: `Worker ${index + 1} · last queue poll`, value: readableTime(worker.last)});
        }
        return fields;
    }

    async function mount(root, config) {
        const container = root.querySelector('.modules-graph-canvas');
        const message = root.querySelector('.modules-graph-message');
        const selection = root.querySelector('.modules-graph-selection');
        const legend = [...root.querySelectorAll('[data-module-status]')];
        let hoveredStatus = null;
        let focusedStatus = null;
        let selectedStatus = null;
        let selectingLegend = false;
        let graph;
        const updateEmphasis = function () {
            if (!root.graph) {
                return;
            }
            const status = hoveredStatus || focusedStatus || selectedStatus;
            root.classList.toggle('modules-graph-legend-preview', Boolean(status));
            legend.forEach(button => {
                button.classList.toggle('is-previewed', button.dataset.moduleStatus === status);
                button.setAttribute('aria-pressed', String(button.dataset.moduleStatus === selectedStatus));
            });
            if (status) {
                const matches = graph.getMutableNodes().filter(node => node.visible && node.getData().status === status);
                graph.emphasiseElements(matches);
                const label = legend.find(button => button.dataset.moduleStatus === status).textContent;
                selection.textContent = `${label} · ${matches.length} ${matches.length === 1 ? 'module' : 'modules'}${status === selectedStatus ? ' selected' : ''}`;
                return;
            }
            const selected = graph.renderer.getGraphInteraction().getSelectedNodes().map(entry => entry.node);
            if (selected.length === 1) {
                const node = selected[0];
                const connected = [...node.getEdgesIn(), ...node.getEdgesOut()];
                graph.emphasiseElements([node, ...connected, ...connected.flatMap(edge => [edge.from, edge.to])]);
                selection.textContent = `${node.id} · inputs and outputs highlighted`;
            } else if (selected.length > 1) {
                graph.emphasiseElements(selected);
                selection.textContent = `${selected.length} modules selected`;
            } else {
                graph.clearEmphasis();
                selection.textContent = 'Select a module to highlight its inputs and outputs.';
            }
        };
        try {
            const response = await fetch(config.graphUrl, {cache: 'no-store'});
            if (!response.ok) {
                throw new Error(`Unable to load the module topology (HTTP ${response.status}).`);
            }
            const data = buildData(await response.json(), config.stats);
            if (!data.nodes.length) {
                throw new Error('No modules are configured or registered.');
            }
            const Pivotick = window.Pivotick;
            if (!Pivotick) {
                throw new Error('The graph viewer could not be loaded.');
            }
            const nodes = data.nodes.map(node => new Pivotick.Node(node.id, node.data, node.style));
            const byId = new Map(nodes.map(node => [node.id, node]));
            const edges = data.edges.map(edge => new Pivotick.Edge(edge.id, byId.get(edge.source), byId.get(edge.target), edge.data, {}, true));
            const layers = Math.max(...data.nodes.map(node => node.data.level)) + 1;
            const rows = new Map();
            data.nodes.forEach(node => {
                rows.set(node.data.level, (rows.get(node.data.level) || 0) + 1);
            });
            const mostRows = Math.max(...rows.values());
            // Measure the full canvas rather than the shorter loading placeholder.
            message.hidden = true;
            const clearFocus = function () {
                selectedStatus = null;
                graph.selectElements([]);
                updateEmphasis();
            };
            graph = new Pivotick(container, {nodes, edges}, {
                layout: {type: 'tree', horizontal: true, depthKey: 'level', spacing: 'manual', levelSpacing: Math.max(1.5, layers * 344 / container.clientWidth), siblingSpacing: Math.max(1.6, mostRows * 120 / container.clientHeight)},
                // Horizontal layers separate the boxes; collision spacing covers their height.
                simulation: {useWorker: false, cooldownTime: 1500, d3CollideRadiusMultiplier: 0.56},
                render: {
                    type: 'svg',
                    renderNode: renderModule,
                    zoomAnimation: false,
                    enableNodeExpansion: false,
                    defaultEdgeStyle: {curveStyle: 'bidirectional', strokeWidth: 1.5},
                },
                UI: {
                    mode: 'full',
                    theme: 'light',
                    sidebar: {collapsed: true},
                    editors: {
                        nodeCreator: {enabled: false},
                        edgeCreator: {enabled: false},
                        nodeEditor: {enabled: false},
                        edgeEditor: {enabled: false},
                    },
                    contextMenu: {enabled: false},
                    filter: {excludeKeys: ['description', 'publish', 'runtimeOnly', 'workers', 'level', 'status']},
                    notes: {enabled: false},
                    history: {enabled: false},
                    minimap: {collapsed: 'auto', position: 'bottom-right'},
                    propertiesPanel: {nodePropertiesMap: properties, edgePropertiesMap: properties},
                    tooltip: {enabled: true, nodePropertiesMap: properties, edgePropertiesMap: properties},
                },
                callbacks: {
                    onNodeSelect: function () {
                        if (!selectingLegend) {
                            selectedStatus = null;
                        }
                        updateEmphasis();
                        graph.UIManager.sidebar.showSidebar();
                    },
                    onNodesSelect: function () {
                        if (!selectingLegend) {
                            selectedStatus = null;
                        }
                        updateEmphasis();
                        graph.UIManager.sidebar.showSidebar();
                    },
                    onNodeBlur: function () {
                        if (!selectingLegend) {
                            selectedStatus = null;
                        }
                        updateEmphasis();
                    },
                    onEdgeSelect: function () {
                        selectedStatus = null;
                        updateEmphasis();
                        graph.UIManager.sidebar.showSidebar();
                    },
                    onCanvasClick: function () {
                        clearFocus();
                    },
                    onBeforeDelete: function () {
                        return {accept: false};
                    },
                },
            });
            root.graph = graph;
            legend.forEach(button => {
                button.disabled = false;
                button.addEventListener('click', function () {
                    selectedStatus = button.dataset.moduleStatus;
                    const matches = graph.getMutableNodes().filter(node => node.visible && node.getData().status === selectedStatus);
                    if (matches.length) {
                        graph.UIManager.sidebar.showSidebar();
                    }
                    selectingLegend = true;
                    try {
                        graph.selectElements(matches);
                    } finally {
                        selectingLegend = false;
                    }
                    updateEmphasis();
                });
                button.addEventListener('mouseenter', function () {
                    hoveredStatus = button.dataset.moduleStatus;
                    updateEmphasis();
                });
                button.addEventListener('mouseleave', function () {
                    hoveredStatus = null;
                    updateEmphasis();
                });
                button.addEventListener('focus', function () {
                    focusedStatus = button.dataset.moduleStatus;
                    updateEmphasis();
                });
                button.addEventListener('blur', function () {
                    focusedStatus = null;
                    updateEmphasis();
                });
            });
            await graph.simulation.waitForSimulationStop();
            graph.renderer.fitAndCenter();
        } catch (error) {
            if (graph) {
                graph.destroy();
            }
            root.graph = null;
            root.classList.remove('modules-graph-legend-preview');
            legend.forEach(button => {
                button.disabled = true;
                button.classList.remove('is-previewed');
                button.setAttribute('aria-pressed', 'false');
            });
            container.replaceChildren();
            message.hidden = false;
            message.classList.add('alert', 'alert-warning');
            message.textContent = `${error.message} The module statistics remain available below. The topology is regenerated when AIL starts.`;
        }
    }

    return {buildData, readableTime, properties, mount};
});

if (typeof document !== 'undefined') {
    document.addEventListener('DOMContentLoaded', function () {
        const root = document.getElementById('modules-graph');
        if (root) {
            const config = JSON.parse(document.getElementById('modules-graph-config').textContent);
            window.AILModulesGraph.mount(root, config);
        }
    });
}
