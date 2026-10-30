/* Pivotick rendering and object previews for the correlation page. */
(function () {
    'use strict';
    const config = JSON.parse(document.getElementById('correlation-config').textContent);
    const all_graph = window.all_graph = {};
    const PivotickGraph = window.Pivotick;
    const PivotickNode = PivotickGraph.Node;
    const PivotickEdge = PivotickGraph.Edge;
    let currentObject = null;

    function build_tooltip_html(title, data) {
        const excludedKeys = ['tags', 'id', 'img', 'svg_icon', 'icon', 'link', 'type', 'tags_safe', 'is_tags_safe'];
        const prettifyKey = function(key) {
            return sanitize_text((key || '').replace(/_/g, ' '));
        };
        const formatDate = function(value) {
            if (typeof value === 'string' && value.length === 8 && /^\d+$/.test(value)) {
                return value.slice(0, 4) + '-' + value.slice(4, 6) + '-' + value.slice(6, 8);
            }
            return sanitize_text(value);
        };
        const buildDetailRow = function(label, value) {
            if (value === null || value === undefined || value === '') {
                return '';
            }
            return '<div class="pivotik-tooltip-row"><span class="pivotik-tooltip-label">' + prettifyKey(label) +
                '</span><span class="pivotik-tooltip-value">' + sanitize_text(value) + '</span></div>';
        };

        let desc = '<div class="card pivotik-tooltip-card">';
        desc = desc + '<div class="card-body p-2">';
        desc = desc + '<div class="pivotik-tooltip-details">';

        if (Object.prototype.hasOwnProperty.call(data, 'status')) {
            const statusLabel = data.status ? 'UP' : 'DOWN';
            const statusClass = data.status ? 'success' : 'danger';
            const statusIcon = data.status ? 'fa-check-circle' : 'fa-times-circle';
            desc = desc + '<div class="pivotik-tooltip-row"><span class="pivotik-tooltip-label">Status</span><span class="pivotik-tooltip-value"><span class="badge badge-' + statusClass + '"><i class="fas ' + statusIcon + ' mr-1"></i>' + statusLabel + '</span></span></div>';
        }

        Object.keys(data).forEach(function(key) {
            if (excludedKeys.includes(key) || key === 'status' || !data[key]) {
                return;
            }
            if (key === 'first_seen' || key === 'last_seen') {
                desc = desc + buildDetailRow(key, formatDate(data[key]));
            } else {
                desc = desc + buildDetailRow(key, data[key]);
            }
        });

        desc = desc + '</div>';

        if (data.tags) {
            desc = desc + '<div class="pivotik-tooltip-tags">';
            data.tags.forEach(function(tag) {
                desc = desc + '<span class="badge badge-warning">' + sanitize_text(tag) + '</span> ';
            });
            desc = desc + '</div>';
        }

        if (data.img) {
            desc = desc + '<div class="pivotik-tooltip-image">';
            if (data.tags_safe) {
                const endpoint = data.type === 'screenshot' ? config.urls.screenshot : data.type === 'favicon' ? config.urls.favicon : config.urls.image;
                desc = desc + '<img src="' + sanitize_text(endpoint + data.img) + '" class="img-thumbnail correlation-tooltip-image object_image" style="max-height: 14rem;"/>';
            } else {
                desc = desc + '<span class="my-2 fa-stack fa-4x"><i class="fas fa-stack-1x fa-image"></i><i class="fas fa-stack-2x fa-ban" style="color:Red"></i></span>';
            }
            desc = desc + '</div>';
        }

        desc = desc + '</div></div>';
        return desc;
    }

    function render_pivotick_tooltip(element) {
        const wrapper = document.createElement('div');
        const elementData = typeof element.getData === 'function' ? (element.getData() || {}) : {};
        if (elementData._misp && all_graph.misp_expansion) {
            return all_graph.misp_expansion.renderDetails(element);
        }
        const isNode = (typeof element.degree === 'function') || !!elementData._ail;
        if (!isNode) {
            const label = sanitize_text((elementData && elementData.label) ? elementData.label : 'Relationship');
            wrapper.innerHTML = '<div class="px-2 py-1"><b>' + label + '</b></div>';
            return wrapper;
        }

        const nodeId = get_node_id(element);
        const title = get_node_text(element);
        if (!nodeId) {
            wrapper.innerHTML = '<div class="px-2 py-1"><b>' + sanitize_text(title || 'Object') + '</b></div>';
            return wrapper;
        }
        const ail = elementData._ail || elementData;

        if (ail.tooltip_html) {
            wrapper.innerHTML = ail.tooltip_html;
            append_misp_annotations(wrapper, element);
            return wrapper;
        }

        wrapper.innerHTML = '<div class="card pivotik-tooltip-card"><div class="card-body p-2"><div class="d-flex align-items-center"><div class="spinner-border spinner-border-sm text-warning mr-2" role="status"></div><span>Loading details...</span></div></div></div>';

        $.getJSON(config.urls.description, {object_id: nodeId},
            function(data) {
                const html = build_tooltip_html(title, data);
                ail.tooltip_html = html;
                wrapper.innerHTML = html;
                append_misp_annotations(wrapper, element);
            }
        ).fail(function(error) {
            wrapper.innerHTML = '<div class="card pivotik-tooltip-card"><div class="card-body p-2"><div class="text-danger"><i class="fas fa-times-circle mr-1"></i>' + sanitize_text(error.statusText || 'Error while loading tooltip') + '</div></div></div>';
        });

        return wrapper;
    }


    function append_misp_annotations(wrapper, element) {
        if (all_graph.misp_expansion?.properties(element).length) {
            wrapper.append(all_graph.misp_expansion.renderDetails(element));
        }
    }


    function get_icon_unicode_value(nodeStyle) {
        return (nodeStyle && (nodeStyle.icon_text || nodeStyle.icon)) || '';
    }

    function get_icon_codepoint(iconValue) {
        if (!iconValue) {
            return null;
        }
        const cp = iconValue.codePointAt(0);
        if (!cp) {
            return null;
        }
        return cp.toString(16).toUpperCase();
    }

    function is_svg_icon(nodeStyle) {
        return nodeStyle && nodeStyle.style === 'svg' && nodeStyle.icon;
    }

    function build_icon_class(nodeStyle) {
        if (is_svg_icon(nodeStyle)) {
            return '';
        }
        const baseClass = (nodeStyle && (nodeStyle.icon_class || nodeStyle.style)) || '';
        const iconValue = get_icon_unicode_value(nodeStyle);
        const codepoint = get_icon_codepoint(iconValue);
        if (!codepoint) {
            return baseClass;
        }
        return (baseClass + ' pvt-ail-icon-' + codepoint).trim();
    }

    function build_svg_icon(nodeStyle) {
        if (is_svg_icon(nodeStyle)) {
            return nodeStyle.icon;
        }
        return undefined;
    }

    function inject_icon_css_rules(nodes) {
        const styleId = 'pivotick-ail-icon-map';
        let styleTag = document.getElementById(styleId);
        if (!styleTag) {
            styleTag = document.createElement('style');
            styleTag.id = styleId;
            document.head.appendChild(styleTag);
        }
        const rules = [];
        nodes.forEach(function(node) {
            if (is_svg_icon(node.style)) {
                return;
            }
            const iconValue = get_icon_unicode_value(node.style);
            const codepoint = get_icon_codepoint(iconValue);
            if (codepoint) {
                rules.push('.pvt-ail-icon-' + codepoint + '::before { content: ' + JSON.stringify(String.fromCodePoint(parseInt(codepoint, 16))) + '; }');
            }
        });
        styleTag.textContent = rules.join('\n');
    }

    const SIDEBAR_HIDDEN_KEYS = new Set([
        'icon',
        'shape',
        'style',
        'text',
        'url',
        'x',
        'y',
        'vx',
        'vy',
        'fx',
        'fy',
        '_ail',
    ]);

    function build_sidebar_properties(element) {
        const data = (element && typeof element.getData === 'function') ? (element.getData() || {}) : (element || {});
        if (data._misp && all_graph.misp_expansion) {
            return all_graph.misp_expansion.properties(element);
        }
        return Object.entries(data)
            .filter(function(entry) {
                const key = entry[0];
                const value = entry[1];
                return key && value !== null && value !== undefined && value !== '' && !SIDEBAR_HIDDEN_KEYS.has(key);
            })
            .map(function(entry) {
                return { name: entry[0], value: entry[1] };
            }).concat(all_graph.misp_expansion?.properties(element) || []);
    }

    function build_group_style(group) {
        const types = Object.keys(group.typeCounts);
        if (types.length !== 1 || !types[0]) {
            return;
        }
        const style = group.members[0]?.getStyle() || {};
        if (!style.iconClass && !style.iconUnicode && !style.svgIcon) {
            return;
        }
        return {
            badges: [{
                position: 'ne',
                color: 'var(--pvt-menu-bg-color)',
                iconClass: style.iconClass,
                iconUnicode: style.iconUnicode,
                svgIcon: style.svgIcon,
                title: types[0] + ' objects',
            }],
        };
    }

    function group_shared_correlations(view) {
        const groups = new Map();
        const rootId = config.object.gid;
        for (const node of view.nodes) {
            const ail = node.getData()._ail;
            if (!ail || node.id === rootId) {
                continue;
            }
            const neighbours = new Set([...view.inNeighbours(node), ...view.outNeighbours(node)].map(neighbour => neighbour.id));
            if (neighbours.size === 0 || neighbours.has(node.id)) {
                continue;
            }
            const type = node.id.split(':', 1)[0];
            groups.set(node.id, JSON.stringify([[...neighbours].sort(), type]));
        }
        return groups;
    }


    function create_graph(data, view) {
        const graphContainer = document.getElementById('graph');

        inject_icon_css_rules(data.nodes);

        const nodeById = {};
        const nodes = data.nodes.map(function(n) {
            nodeById[n.id] = new PivotickNode(n.id, {
                ...n,
                label: n.text,
                _ail: n,
            }, {
                color: n.style.node_color || n.style.color,
                size: n.style.node_radius || n.style.radius || 5,
                iconClass: build_icon_class(n.style),
                svgIcon: build_svg_icon(n.style),
                text: '',
                textColor: '#000000',
            });
            return nodeById[n.id];
        });

        const edges = data.links.map(function(l, i) {
            const sourceId = typeof l.source === 'object' ? l.source.id : l.source;
            const targetId = typeof l.target === 'object' ? l.target.id : l.target;
            return new PivotickEdge(
                'e' + i,
                nodeById[sourceId],
                nodeById[targetId],
                { label: l.relationship || '' },
                {},
                false
            );
        }).filter(edge => edge.from && edge.to);

        currentObject = null;
        all_graph.misp_expansion?.destroy();
        all_graph.legend?.destroy();
        all_graph.node_graph?.renderer.getCanvasSelection().interrupt();
        all_graph.node_graph?.destroy();
        graphContainer.replaceChildren();
        all_graph.node_graph = new PivotickGraph(graphContainer, { nodes: nodes, edges: edges }, {
            render: {
                type: 'svg',
                enableNodeExpansion: false,
                groupStyle: build_group_style,
                defaultEdgeStyle: {
                    markerEnd: "",
                    markerStart: "",
                    curveStyle: 'straight',
                },
            },
            UI: {
                mode: 'full',
                theme: 'dark',
                legend: false,
                simplify: {
                    openConfirmAbove: Number.POSITIVE_INFINITY,
                    typeOf: function(node) {
                        const ail = node.getData()._ail;
                        return ail ? ail.id.split(':', 1)[0] : undefined;
                    },
                    rules: [{
                        kind: 'custom',
                        id: 'shared-correlations',
                        label: 'Shared correlations',
                        description: 'Objects of the same type with the same set of neighbours in the displayed graph.',
                        minSize: 10,
                        partition: group_shared_correlations,
                    }],
                },
                editors: {
                    nodeCreator: { enabled: false },
                    edgeCreator: { enabled: false },
                },
                tooltip: {
                    enabled: true,
                    render: render_pivotick_tooltip,
                },
                sidebar: {
                    collapsed: true,
                },
                table: {
                    columns: [
                        {key: 'name', label: 'Object', accessor: get_node_text, filterable: true},
                        {key: 'type', label: 'Type', type: 'select', accessor: node => node.getData()._ail ? node.id.split(':', 1)[0] : node.getData().type, filterable: true},
                        {key: 'correlations', label: 'Loaded correlations', type: 'numberRange', accessor: node => node.degree(), filterable: true},
                        {key: 'visibility', label: 'Visibility', accessor: node => !node.visible ? 'Hidden' : node.canvasRepresentative() !== node ? 'Packed' : 'Visible'},
                    ],
                    edgeColumns: [
                        {key: 'source', label: 'From', accessor: edge => get_node_text(edge.from), filterable: true},
                        {key: 'target', label: 'To', accessor: edge => get_node_text(edge.to), filterable: true},
                    ],
                },
                propertiesPanel: {
                    nodePropertiesMap: build_sidebar_properties,
                    edgePropertiesMap: build_sidebar_properties,
                },

            },
            callbacks: {
                onNodeDbclick: doubleclick,
                onNodeHoverIn: function(event, node) {
                    currentObject = {id: get_node_id(node), node: node};
                },
                onNodeHoverOut: function() {
                    currentObject = null;
                },
                onCanvasClick: function() {
                    currentObject = null;
                },
            },
        });

        all_graph.legend = AILCorrelationGraphLegend.attach(all_graph.node_graph, document.getElementById('correlation-graph-legend'));
        all_graph.misp_expansion = AILMISPGraphPivots.attach(all_graph.node_graph, document.getElementById('misp-expansion-controls'));

        const graph = all_graph.node_graph;
        for (const rule of view?.rules || []) {
            graph.simplify.setRuleEnabled(rule.id, rule.enabled);
            graph.simplify.setRuleMinSize(rule.id, rule.minSize);
        }
        const open = new Set(view?.open || []);
        graph.simplify.getGroups().forEach(group => {
            if (open.has(all_graph.page.groupKey(group))) {
                graph.simplify.open(group.id);
            }
        });
        return graph;
    }

    function get_node_data(nodeLike) {
        if (!nodeLike) {
            return {};
        }
        if (typeof nodeLike.getData === 'function') {
            return nodeLike.getData() || {};
        }
        return nodeLike;
    }

    function get_node_id(nodeLike) {
        if (!nodeLike) {
            return null;
        }
        if (nodeLike.id) {
            return nodeLike.id;
        }
        const data = get_node_data(nodeLike);
        return data.id || (data._ail && data._ail.id) || null;
    }

    function get_node_text(nodeLike) {
        const data = get_node_data(nodeLike);
        const ail = data._ail || {};
        return ail.text || data.label || get_node_id(nodeLike) || '';
    }

    function doubleclick(event, node) {
        const data = get_node_data(node);
        if (data._misp) {
            return;
        }
        const ail = data._ail || data;
        if (ail.url) {
            window.open(ail.url, '_blank', 'noopener');
        }
    }

    $(function() {
        all_graph.page = AILCorrelationPage.attach(config, create_graph);
        all_graph.page.load({settings: config.state, url: all_graph.page.appliedUrl, history: 'none'});
        const activity = document.getElementById('correlation-activity');
        if (activity && config.urls.activity) {
            activity.addEventListener('toggle', function() {
                if (activity.open && !activity.dataset.loaded && typeof window.create_line_chart === 'function') {
                    activity.dataset.loaded = 'true';
                    window.create_line_chart('graph_line', config.urls.activity);
                }
            });
        }
        document.addEventListener('keydown', function(event) {
            if (event.key.toLowerCase() !== 'h' || event.ctrlKey || event.metaKey || event.altKey || event.target.closest('input, textarea, select, [contenteditable]')) {
                return;
            }
            if (currentObject && get_node_data(currentObject.node)._ail && !AILMISPGraph.isExpansionNode(currentObject.node)) {
                event.preventDefault();
                all_graph.page.hideObjects([currentObject.node]);
            }
        });
    });
})();
