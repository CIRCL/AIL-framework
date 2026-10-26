/* A live object-type legend shared by the Pivotick correlation graphs. */
(function () {
    'use strict';

    function objectType(node) {
        const data = node.getData();
        if (data._ail) {
            return data._ail.id.split(':', 1)[0];
        }
        return data._misp ? 'MISP: ' + data.type : data.type || 'Object';
    }

    function iconPreview(style) {
        const swatch = document.createElement('span');
        swatch.className = 'correlation-legend-icon';
        swatch.setAttribute('aria-hidden', 'true');
        swatch.style.backgroundColor = style.color;
        swatch.style.color = style.iconColor || '#000000';
        if (style.svgIcon) {
            // These are the same application-provided SVG icons used by the renderer.
            swatch.innerHTML = style.svgIcon;
        } else if (style.iconUnicode) {
            swatch.classList.add('fas');
            swatch.textContent = style.iconUnicode;
        } else if (style.iconClass) {
            const icon = document.createElement('i');
            icon.className = style.iconClass;
            swatch.appendChild(icon);
        }
        return swatch;
    }

    class CorrelationGraphLegend {
        constructor(graph, container) {
            this.graph = graph;
            this.container = container;
            this.list = container.querySelector('[data-legend-types]');
            this.clear = container.querySelector('[data-legend-clear]');
            this.interaction = graph.renderer.getGraphInteraction();
            this.entries = new Map();
            this.frame = null;
            this.rebuild = () => {
                if (this.frame === null) {
                    this.frame = requestAnimationFrame(() => {
                        this.frame = null;
                        this.render();
                    });
                }
            };
            this.sync = () => this.syncSelection();
            this.onClick = event => {
                const button = event.target.closest('[data-legend-type]');
                if (!button) {
                    return;
                }
                const nodes = this.nodes().filter(node => objectType(node) === button.dataset.legendType);
                if (event.ctrlKey || event.metaKey || event.shiftKey) {
                    graph.addToSelection(nodes);
                } else {
                    graph.selectElements(nodes);
                }
            };
            this.onClear = () => graph.selectElements([]);
            this.list.addEventListener('click', this.onClick);
            this.clear.addEventListener('click', this.onClear);
            graph.on('ready', this.rebuild);
            graph.on('dataBatchChanged', this.rebuild);
            graph.queryEngine.on('filterChange', this.rebuild);
            this.selectionEvents = ['selectNode', 'unselectNode', 'selectNodes', 'unselectNodes', 'selectEdges', 'unselectEdges'];
            this.selectionEvents.forEach(name => this.interaction.on(name, this.sync));
            this.render();
        }

        nodes() {
            // Packed members remain real, visible nodes; synthetic group handles do not count.
            return this.graph.getMutableNodes().filter(node => node.visible && !node.isGroup);
        }

        render() {
            const entries = new Map();
            this.nodes().forEach(node => {
                const type = objectType(node);
                if (!entries.has(type)) {
                    entries.set(type, {nodes: [], icons: new Map()});
                }
                const entry = entries.get(type);
                entry.nodes.push(node);
                const style = node.getStyle();
                const iconKey = JSON.stringify([style.color, style.iconClass, style.iconUnicode, style.svgIcon]);
                entry.icons.set(iconKey, style);
            });
            this.entries = new Map([...entries].sort(([first], [second]) => first.localeCompare(second)));
            this.list.replaceChildren();
            this.entries.forEach((entry, type) => {
                const button = document.createElement('button');
                button.type = 'button';
                button.className = 'correlation-legend-type';
                button.dataset.legendType = type;
                button.title = 'Select all ' + entry.nodes.length + ' ' + type + ' objects';
                const icons = document.createElement('span');
                icons.className = 'correlation-legend-icons';
                entry.icons.forEach(style => icons.appendChild(iconPreview(style)));
                const label = document.createElement('span');
                label.className = 'correlation-legend-label';
                label.textContent = type;
                const count = document.createElement('span');
                count.className = 'correlation-legend-count';
                count.textContent = entry.nodes.length;
                button.append(icons, label, count);
                entry.button = button;
                this.list.appendChild(button);
            });
            this.container.hidden = this.entries.size === 0;
            this.syncSelection();
        }

        syncSelection() {
            const selected = new Set();
            const collect = node => {
                if (node.isGroup) {
                    node.info.members.forEach(collect);
                } else {
                    selected.add(node.id);
                }
            };
            this.interaction.getSelectedNodes().forEach(({node}) => collect(node));
            this.entries.forEach(entry => {
                const count = entry.nodes.filter(node => selected.has(node.id)).length;
                entry.button.setAttribute('aria-pressed', count === 0 ? 'false' : count === entry.nodes.length ? 'true' : 'mixed');
            });
            this.clear.disabled = selected.size === 0 && this.interaction.getSelectedEdges().length === 0;
        }

        destroy() {
            if (this.frame !== null) {
                cancelAnimationFrame(this.frame);
            }
            this.list.removeEventListener('click', this.onClick);
            this.clear.removeEventListener('click', this.onClear);
            this.graph.off('ready', this.rebuild);
            this.graph.off('dataBatchChanged', this.rebuild);
            this.graph.queryEngine.off('filterChange', this.rebuild);
            this.selectionEvents.forEach(name => this.interaction.off(name, this.sync));
        }
    }

    window.AILCorrelationGraphLegend = {
        attach: function(graph, container) {
            return new CorrelationGraphLegend(graph, container);
        },
    };
})();
