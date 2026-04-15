var da = Object.defineProperty;
var ua = (i, t, e) => t in i ? da(i, t, { enumerable: !0, configurable: !0, writable: !0, value: e }) : i[t] = e;
var f = (i, t, e) => ua(i, typeof t != "symbol" ? t + "" : t, e);
function st(i, ...t) {
  if (typeof i == "string")
    return i;
  if (typeof i == "function") {
    const e = i(...t);
    return typeof e == "string" ? e : void 0;
  }
}
function ni(i, ...t) {
  if (typeof i == "boolean")
    return i;
  if (typeof i == "function") {
    const e = i(...t);
    return typeof e == "boolean" ? e : void 0;
  }
}
function ri(i, ...t) {
  if (typeof i == "number")
    return i;
  if (typeof i == "function") {
    const e = i(...t);
    return typeof e == "number" ? e : void 0;
  }
}
function Jr(i, ...t) {
  if (Array.isArray(i))
    return i;
  if (typeof i == "function") {
    const e = i(...t);
    return Array.isArray(e) ? e : [];
  }
  return [];
}
function St(i, ...t) {
  if (i instanceof HTMLElement)
    return i;
  if (typeof i == "string") {
    const e = document.createElement("template"), n = i.trim();
    if (e.innerHTML = n, e.content.firstElementChild)
      return e.content.firstElementChild;
    const r = document.createElement("span");
    return r.textContent = n, r;
  } else if (typeof i == "function") {
    const e = i(...t);
    if (typeof e == "string") {
      const n = document.createElement("template");
      if (n.innerHTML = e, n.content.firstElementChild)
        return n.content.firstElementChild;
      const r = document.createElement("span");
      return r.textContent = e, r;
    } else
      return e;
  }
}
function ts(i) {
  const t = document.createElement("i");
  t.className = i, document.body.appendChild(t);
  let r = getComputedStyle(t).getPropertyValue("--fa").replace(/["']/g, "");
  const s = parseInt(r.slice(1), 16);
  return r = String.fromCharCode(s), document.body.removeChild(t), r;
}
function ft(i) {
  i.variant = i.variant ?? "primary";
  const {
    variant: t,
    size: e,
    onClick: n,
    onClickArgs: r,
    iconUnicode: s,
    iconClass: o,
    svgIcon: a,
    imagePath: c,
    text: l,
    ...h
  } = i, d = document.createElement("button");
  d.classList.add("pivotick-button"), d.classList.add(`pivotick-button-${t}`), e && d.classList.add(`pivotick-button-${e}`);
  for (const [g, v] of Object.entries(h))
    g === "class" ? Array.isArray(v) ? d.classList.add(...v) : d.classList.add(String(v)) : g in d ? d[g] = v : d.setAttribute(g, String(v));
  let u;
  s && (u = Y({ iconUnicode: s })), o && (u = Y({ iconClass: o })), a && (u = Y({ svgIcon: a })), c && (u = Y({ imagePath: c })), u && d.append(u);
  const p = document.createElement("text");
  if (l && (u && (u.style.marginRight = "0.1em"), p.textContent = l), d.append(p), typeof n == "function") {
    const g = r ?? [];
    d.addEventListener("click", (v) => {
      n(v, ...g);
    });
  }
  return d;
}
const pa = "outline-primary";
function fa(i, t = {}, e = []) {
  const n = document.createElementNS("http://www.w3.org/2000/svg", i);
  for (const [r, s] of Object.entries(t))
    Array.isArray(s) ? n.setAttribute(r, s.join(" ")) : n.setAttribute(r, s.toString());
  for (const r of e)
    typeof r == "string" ? n.appendChild(document.createTextNode(r)) : n.appendChild(r);
  return n;
}
function T(i, t = {}, e = []) {
  const n = document.createElement(i);
  for (const [r, s] of Object.entries(t))
    Array.isArray(s) ? n.setAttribute(r, s.join(" ")) : n.setAttribute(r, s.toString());
  for (const r of e)
    typeof r == "string" ? n.appendChild(document.createTextNode(r)) : n.appendChild(r);
  return n;
}
function ot(i) {
  const t = document.createElement("template");
  return t.innerHTML = i.trim(), t.content.firstElementChild;
}
function si(i, t) {
  const e = T("dl", { class: "pvt-property-list" });
  for (const n of i) {
    const r = St(n.name, t) || "", s = St(n.value, t) || "", o = T(
      "dl",
      {
        class: "pvt-property-row"
      },
      [
        T("dt", { class: "pvt-property-name" }, [r]),
        T("dd", { class: "pvt-property-value" }, [s])
      ]
    );
    e.append(o);
  }
  return e;
}
function We(i, t, e) {
  const n = T("div", { class: "pvt-action-list" }), r = Array.isArray(e) ? e[0] : e;
  return t.forEach((s) => {
    if (s.visible = s.visible ?? !0, ni(s.visible, r) ?? !0) {
      const a = ga(i, s, e);
      n.appendChild(a);
    }
  }), n;
}
function Ke(i, t, e) {
  const n = T("div", { class: "pvt-action-list" }), r = Array.isArray(e) ? e[0] : e;
  return t.forEach((s) => {
    if (s.visible = s.visible ?? !0, ni(s.visible, r) ?? !0) {
      const a = ma(i, s, e);
      n.appendChild(a);
    }
  }), n;
}
function ga(i, t, e) {
  t.variant = t.variant ?? pa;
  const { onclick: n, ...r } = t, s = T(
    "span",
    {
      class: ["pvt-action-item", `pvt-action-item-${t.variant}`],
      style: `${t.flushRight ? "margin-left: auto;" : ""}`
    },
    [
      ft({
        size: "sm",
        ...r
      })
    ]
  );
  return typeof n == "function" && s.addEventListener("click", (o) => {
    n.call(i, o, e);
  }), s;
}
function ma(i, t, e) {
  const n = T(
    "div",
    {
      class: ["pvt-action-item", `pvt-action-item-${t.variant}`]
    },
    [
      Y({ fixedWidth: !0, ...t }),
      T("span", {
        class: "pvt-action-text",
        title: t.title ?? ""
      }, [t.text ?? ""])
    ]
  );
  return typeof t.onclick == "function" && n.addEventListener("click", (r) => {
    t.onclick.call(i, r, e);
  }), n;
}
function Cn(i = 8, t = "id-") {
  const e = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz", n = e + "0123456789-_";
  let r = e.charAt(Math.floor(Math.random() * e.length));
  for (let s = 1; s < i; s++)
    r += n.charAt(Math.floor(Math.random() * n.length));
  return `${t}${r}`;
}
function Y(i) {
  const t = document.createElement("span");
  if (t.classList.add("pvt-icon"), i.fixedWidth && t.classList.add("fixed-width"), i.iconUnicode || i.iconClass) {
    const e = document.createElement("text");
    i.iconUnicode && (e.className = "icon icon-unicode"), i.iconClass && (e.className = `icon ${i.iconClass ?? ""}`), i.iconUnicode && (e.textContent = i.iconUnicode ?? ts(i.iconClass ?? "") ?? "☐"), t.append(e);
  } else if (i.svgIcon) {
    const e = document.createElement("template");
    e.innerHTML = i.svgIcon.trim();
    const n = e.content.firstElementChild;
    n.setAttribute("width", "100%"), n.setAttribute("height", "100%"), t.style.display = "inline-flex", t.style.alignItems = "center", t.style.justifyContent = "center", t.style.width = "1em", t.append(n);
  } else if (i.imagePath) {
    const e = document.createElement("img");
    e.src = i.imagePath, t.style.display = "inline-flex", t.style.alignItems = "center", t.style.justifyContent = "center", t.style.width = "1em", t.append(e);
  }
  return t;
}
function va(i, t, e, n = {}) {
  let r = !1, s = 0, o = 0, a = 0, c = 0, l = null, h = null;
  t.classList.add("draggable"), t.addEventListener("mousedown", (p) => {
    var y;
    const g = new AbortController(), { signal: v } = g;
    r = !0, t.style.transition = "none", s = p.clientX, o = p.clientY, a = i.offsetLeft, c = i.offsetTop, l = i.getBoundingClientRect(), h = e.getBoundingClientRect(), (y = n.onDragStart) == null || y.call(n, p, i), document.addEventListener("mousemove", d, { signal: v }), document.addEventListener("mouseup", (b) => {
      g.abort(), u(b);
    }, { signal: v });
  });
  function d(p) {
    var C;
    if (!r || !h || !l) return;
    const g = p.clientX - s, v = p.clientY - o;
    let y = a + g, b = c + v;
    const x = l.width, S = l.height;
    y = Math.max(h.left, Math.min(y, h.right - x)), b = Math.max(h.top, Math.min(b, h.bottom - S)), i.style.left = y + "px", i.style.top = b + "px", (C = n.onDrag) == null || C.call(n, p, i);
  }
  function u(p) {
    var g;
    r = !1, i.style.transition = "", (g = n.onDragStop) == null || g.call(n, p, i);
  }
}
let Mt = class es {
  /**
   * Create a new Node instance.
   * @param id - Unique identifier for the node
   * @param data - Optional data payload associated with the node
   */
  constructor(t, e, n, r = Cn(), s = []) {
    f(this, "id");
    f(this, "data");
    f(this, "children");
    f(this, "style");
    f(this, "edgesOut");
    f(this, "edgesIn");
    f(this, "defaultCircleRadius", 10);
    // Layout/physics properties
    f(this, "x");
    f(this, "y");
    f(this, "vx");
    f(this, "vy");
    f(this, "fx");
    f(this, "fy");
    f(this, "weight");
    f(this, "frozen");
    f(this, "visible");
    f(this, "expanded");
    /** True if this node is a child within a collapsed cluster */
    f(this, "isChild");
    f(this, "childrenDepth");
    /** True if this node has child nodes */
    f(this, "isParent");
    /** Reference to the parent cluster node (if this node is a child) */
    f(this, "parentNode");
    /**
     * Reference to the main graph node when this node is a clone in a subgraph.
     * Used for syncing position updates from subgraph back to main graph.
     */
    f(this, "_original_object");
    /**
     * Reference to the deepest sub graph node.
     * Used for checking state of this node in its subgraph
     */
    f(this, "_deepest_node_clone");
    /** The subgraph graph instance created when expanding this node */
    f(this, "_subgraph");
    f(this, "_circleRadius", this.defaultCircleRadius);
    f(this, "_circleRadiusCollapsed", this.defaultCircleRadius);
    f(this, "_dirty");
    f(this, "domID");
    this.id = t, this.domID = r, this.data = e ?? {}, this.style = n ?? {}, this.children = [], this.isParent = !1, this.setChildren(s), this._dirty = !0, this.frozen = !1, this.visible = !0, this.expanded = !1, this.isChild = !1, this.childrenDepth = 0, this.edgesOut = /* @__PURE__ */ new Set(), this.edgesIn = /* @__PURE__ */ new Set();
  }
  /**
   * Get the node's data.
   */
  getData() {
    return this.data;
  }
  /**
   * Update the node's data.
   * @param newData - New data to set
   */
  setData(t) {
    this.data = t, this.markDirty();
  }
  /**
   * Merge partial data into the current node data.
   * Useful for updating only parts of the data.
   * @param partialData - Partial data object to merge
   */
  updateData(t) {
    this.data = { ...this.data, ...t }, this.markDirty();
  }
  /**
   * @private
   */
  registerEdgeOut(t) {
    this.edgesOut.add(t);
  }
  /**
   * @private
   */
  registerEdgeIn(t) {
    this.edgesIn.add(t);
  }
  /**
   * @private
   */
  emptyEdges() {
    this.edgesOut.clear(), this.edgesIn.clear();
  }
  getConnectedNodes() {
    return [...this.edgesOut].map((t) => t.to);
  }
  getConnectingNodes() {
    return [...this.edgesIn].map((t) => t.from);
  }
  getEdgesOut() {
    return [...this.edgesOut];
  }
  getEdgesIn() {
    return [...this.edgesIn];
  }
  /**
   * Get the node's data.
   */
  getStyle() {
    return this.style;
  }
  /**
   * Update the node's data.
   * @param newStyle - New data to set
   */
  setStyle(t) {
    this.style = t, this.markDirty();
  }
  /**
   * Merge partial data into the current node data.
   * Useful for updating only parts of the data.
   * @param partialStyle - Partial data object to merge
   */
  updateStyle(t) {
    this.style = { ...this.style, ...t }, this.markDirty();
  }
  getGraphElement() {
    return document ? document.getElementById(`node-${this.domID}`) : null;
  }
  /**
   * Convert node to a simple JSON object representation.
   * @param dataOnly - default: false
   */
  toDict(t = !1) {
    const e = {
      id: this.id,
      data: this.data,
      style: this.style,
      weight: this.weight
      // expanded: this.expanded,
    };
    return t || (e.x = this.x, e.y = this.y, e.vx = this.vx, e.vy = this.vy, e.fx = this.fx, e.fy = this.fy), this.hasChildren() && (e.children = this.children.map((n) => n.toDict(t))), e;
  }
  clone() {
    const t = { ...this.data }, e = { ...this.style }, n = new es(this.id, t, e);
    return n.x = this.x, n.y = this.y, n.vx = this.vx, n.vy = this.vy, n.fx = this.fx, n.fy = this.fy, n.weight = this.weight, n.frozen = this.frozen, n.visible = this.visible, n.expanded = this.expanded, n.isChild = this.isChild, n.childrenDepth = this.childrenDepth, n.isParent = this.isParent, n.parentNode = this.parentNode, n._circleRadius = this._circleRadius, n.children = this.children.map((r) => r.clone()), n;
  }
  /**
   * @private
   */
  markDirty() {
    this._dirty = !0;
  }
  /**
   * @private
   */
  clearDirty() {
    this._dirty = !1;
  }
  /**
   * @private
   */
  isDirty() {
    return this._dirty;
  }
  freeze() {
    this.frozen = !0, this.fx = this.x, this.fy = this.y;
  }
  unfreeze() {
    this.frozen = !1, this.fx = void 0, this.fy = void 0;
  }
  toggleVisibility(t) {
    t ? this.show() : this.hide(), this.markDirty();
  }
  show() {
    this.visible = !0;
  }
  hide() {
    this.visible = !1;
  }
  toggleExpand(t) {
    t === void 0 ? this.expanded ? this.collapse() : this.expand() : t ? this.expand() : this.collapse(), this.markDirty();
  }
  expand() {
    this.expanded = !0, this._original_object && (this._original_object.expanded = !0);
  }
  collapse() {
    this.expanded = !1, this._original_object && (this._original_object.expanded = !1);
  }
  degree() {
    return this.edgesOut.size + this.edgesIn.size;
  }
  setCircleRadius(t) {
    this._circleRadius = t;
  }
  getCircleRadius() {
    return this._circleRadius;
  }
  setCircleRadiusCollapsed(t) {
    this._circleRadiusCollapsed = t;
  }
  getCircleRadiusCollapsed() {
    return this._circleRadiusCollapsed;
  }
  setChildren(t) {
    this.children = t, this.hasChildren() ? this.isParent = !0 : this.isParent = !1;
  }
  hasChildren() {
    return this.children.length > 0;
  }
  markAsChild(t, e) {
    this.isChild = !0, this.childrenDepth = e, this.parentNode = t;
  }
  markAsParent() {
    this.isParent = !0;
  }
  /**
   * Sets the subgraph instance (when opening a cluster).
   * @private
   */
  setSubgraph(t) {
    this._subgraph = t;
  }
  /**
   * Gets the subgraph instance created from this node.
   * Returns undefined if this node didn't created a subgraph.
   * @private
   */
  getSubgraph() {
    return this._subgraph;
  }
  /**
   * Sets a reference to the original node from the main graph.
   * Used when this node is a clone in a subgraph to enable position syncing.
   * @private
   */
  setOriginalObject(t) {
    this._original_object = t;
  }
  /**
   * Gets the reference to the original node from the main graph.
   * Returns undefined if this is not a subgraph clone.
   * @private
   */
  getOriginalObject() {
    return this._original_object;
  }
  /**
   * Sets a reference to the original node from the main graph.
   * Used when this node is a clone in a subgraph to enable position syncing.
   * @private
   */
  setDeepestNodeClone(t) {
    this._deepest_node_clone = t;
  }
  /**
   * Gets the reference to the original node from the main graph.
   * Returns undefined if this is not a subgraph clone.
   * @private
   */
  getDeepestNodeClone() {
    return this._deepest_node_clone;
  }
};
class _t {
  /**
   * Create a new Edge instance.
   * @param id - Unique identifier for the edge
   * @param from - Source node
   * @param to - Target node
   * @param data - Optional data payload for the edge
   * @param style - Optional style for the edge
   */
  constructor(t, e, n, r, s, o = null, a) {
    f(this, "id");
    f(this, "from");
    f(this, "to");
    f(this, "directed");
    f(this, "data");
    f(this, "style");
    f(this, "visible");
    /** True if this is a synthetic edge (placeholder for collapsed cluster child) */
    f(this, "isSynthetic");
    /** The actual child node this synthetic edge points to (for expansion logic) */
    f(this, "syntheticTerminalNode");
    f(this, "_original_object");
    f(this, "_subgraphFromNode");
    f(this, "_subgraphToNode");
    f(this, "_dirty");
    f(this, "domID");
    this.id = t, this.domID = Cn(), this.from = e, this.to = n, this.directed = o, this.data = r ?? {}, this.style = s ?? {}, this.visible = !0, this._dirty = !0, this.isSynthetic = a !== void 0, this.syntheticTerminalNode = a, this.from.registerEdgeOut(this), this.to.registerEdgeIn(this);
  }
  /** Required by d3-force */
  get source() {
    return this.from;
  }
  get target() {
    return this.to;
  }
  /**
   * Get the edge's data.
   */
  getData() {
    return this.data;
  }
  /**
   * Update the edge's data.
   * @param newData - New data to set
   */
  setData(t) {
    this.data = t, this.markDirty();
  }
  /**
   * Merge partial data into the current edge data.
   * @param partialData - Partial data object to merge
   */
  updateData(t) {
    this.data = { ...this.data, ...t }, this.markDirty();
  }
  /**
   * Get the edge's style.
   */
  getStyle() {
    return this.style;
  }
  /**
   * Get the edge's style.
   */
  getEdgeStyle() {
    var t;
    return ((t = this.style) == null ? void 0 : t.edge) ?? {};
  }
  /**
   * Get the edge's label style if available.
   */
  getLabelStyle() {
    var t;
    return ((t = this.style) == null ? void 0 : t.label) ?? {};
  }
  /**
   * Update the edge's style.
   * @param newStyle - New style to set
   */
  setStyle(t) {
    this.style = t, this.markDirty();
  }
  /**
   * Merge partial style into the current edge style.
   * Useful for updating only parts of the style.
   * @param partialStyle - Partial style object to merge
   */
  updateStyle(t) {
    this.style = {
      ...this.style,
      ...t
    }, this.markDirty();
  }
  getGraphElement() {
    return document ? document.getElementById(`edge-${this.domID}`) : null;
  }
  setFrom(t) {
    this.from = t;
  }
  setTo(t) {
    this.to = t;
  }
  /**
   * Convert edge to a simple JSON object representation.
   */
  toDict() {
    return {
      id: this.id,
      from: this.from.id,
      to: this.to.id,
      data: this.data,
      style: this.style
    };
  }
  clone() {
    const t = { ...this.data }, e = { ...this.style }, n = new _t(
      this.id,
      this.from.clone(),
      this.to.clone(),
      t,
      e,
      this.directed
    );
    return n.visible = this.visible, n;
  }
  markDirty() {
    this._dirty = !0;
  }
  clearDirty() {
    this._dirty = !1;
  }
  isDirty() {
    return this._dirty;
  }
  toggleVisibility(t) {
    t ? this.show() : this.hide(), this.markDirty();
  }
  show() {
    this.visible = !0;
  }
  hide() {
    this.visible = !1;
  }
  /**
   * Sets a reference to the original node from the main graph.
   * Used when this node is a clone in a subgraph to enable position syncing.
   * @private
   */
  setOriginalObject(t) {
    this._original_object = t;
  }
  /**
   * Gets the reference to the original node from the main graph.
   * Returns undefined if this is not a subgraph clone.
   * @private
   */
  getOriginalObject() {
    return this._original_object;
  }
  /**
   * Sets a reference to the subgraph node from the main graph.
   * Used when the FROM node has a clone in a subgraph
   * @private
   */
  setSubgraphFromNode(t) {
    this._subgraphFromNode = t;
  }
  /**
   * Sets a reference to the subgraph node from the main graph.
   * Used when the TO node has a clone in a subgraph
   * @private
   */
  setSubgraphToNode(t) {
    this._subgraphToNode = t;
  }
  /**
   * Gets the reference to the subgraph node from the main graph.
   * @private
   */
  getSubgraphFromNode() {
    return this._subgraphFromNode;
  }
  /**
   * Gets the reference to the subgraph node from the main graph.
   * @private
   */
  getSubgraphToNode() {
    return this._subgraphToNode;
  }
}
var on = "http://www.w3.org/1999/xhtml";
const ir = {
  svg: "http://www.w3.org/2000/svg",
  xhtml: on,
  xlink: "http://www.w3.org/1999/xlink",
  xml: "http://www.w3.org/XML/1998/namespace",
  xmlns: "http://www.w3.org/2000/xmlns/"
};
function vi(i) {
  var t = i += "", e = t.indexOf(":");
  return e >= 0 && (t = i.slice(0, e)) !== "xmlns" && (i = i.slice(e + 1)), ir.hasOwnProperty(t) ? { space: ir[t], local: i } : i;
}
function ya(i) {
  return function() {
    var t = this.ownerDocument, e = this.namespaceURI;
    return e === on && t.documentElement.namespaceURI === on ? t.createElement(i) : t.createElementNS(e, i);
  };
}
function ba(i) {
  return function() {
    return this.ownerDocument.createElementNS(i.space, i.local);
  };
}
function is(i) {
  var t = vi(i);
  return (t.local ? ba : ya)(t);
}
function wa() {
}
function Mn(i) {
  return i == null ? wa : function() {
    return this.querySelector(i);
  };
}
function xa(i) {
  typeof i != "function" && (i = Mn(i));
  for (var t = this._groups, e = t.length, n = new Array(e), r = 0; r < e; ++r)
    for (var s = t[r], o = s.length, a = n[r] = new Array(o), c, l, h = 0; h < o; ++h)
      (c = s[h]) && (l = i.call(c, c.__data__, h, s)) && ("__data__" in c && (l.__data__ = c.__data__), a[h] = l);
  return new wt(n, this._parents);
}
function Ca(i) {
  return i == null ? [] : Array.isArray(i) ? i : Array.from(i);
}
function Ma() {
  return [];
}
function ns(i) {
  return i == null ? Ma : function() {
    return this.querySelectorAll(i);
  };
}
function Ea(i) {
  return function() {
    return Ca(i.apply(this, arguments));
  };
}
function Sa(i) {
  typeof i == "function" ? i = Ea(i) : i = ns(i);
  for (var t = this._groups, e = t.length, n = [], r = [], s = 0; s < e; ++s)
    for (var o = t[s], a = o.length, c, l = 0; l < a; ++l)
      (c = o[l]) && (n.push(i.call(c, c.__data__, l, o)), r.push(c));
  return new wt(n, r);
}
function rs(i) {
  return function() {
    return this.matches(i);
  };
}
function ss(i) {
  return function(t) {
    return t.matches(i);
  };
}
var _a = Array.prototype.find;
function ka(i) {
  return function() {
    return _a.call(this.children, i);
  };
}
function Na() {
  return this.firstElementChild;
}
function Aa(i) {
  return this.select(i == null ? Na : ka(typeof i == "function" ? i : ss(i)));
}
var Ia = Array.prototype.filter;
function La() {
  return Array.from(this.children);
}
function Oa(i) {
  return function() {
    return Ia.call(this.children, i);
  };
}
function Ta(i) {
  return this.selectAll(i == null ? La : Oa(typeof i == "function" ? i : ss(i)));
}
function Pa(i) {
  typeof i != "function" && (i = rs(i));
  for (var t = this._groups, e = t.length, n = new Array(e), r = 0; r < e; ++r)
    for (var s = t[r], o = s.length, a = n[r] = [], c, l = 0; l < o; ++l)
      (c = s[l]) && i.call(c, c.__data__, l, s) && a.push(c);
  return new wt(n, this._parents);
}
function os(i) {
  return new Array(i.length);
}
function Da() {
  return new wt(this._enter || this._groups.map(os), this._parents);
}
function oi(i, t) {
  this.ownerDocument = i.ownerDocument, this.namespaceURI = i.namespaceURI, this._next = null, this._parent = i, this.__data__ = t;
}
oi.prototype = {
  constructor: oi,
  appendChild: function(i) {
    return this._parent.insertBefore(i, this._next);
  },
  insertBefore: function(i, t) {
    return this._parent.insertBefore(i, t);
  },
  querySelector: function(i) {
    return this._parent.querySelector(i);
  },
  querySelectorAll: function(i) {
    return this._parent.querySelectorAll(i);
  }
};
function Fa(i) {
  return function() {
    return i;
  };
}
function za(i, t, e, n, r, s) {
  for (var o = 0, a, c = t.length, l = s.length; o < l; ++o)
    (a = t[o]) ? (a.__data__ = s[o], n[o] = a) : e[o] = new oi(i, s[o]);
  for (; o < c; ++o)
    (a = t[o]) && (r[o] = a);
}
function Ba(i, t, e, n, r, s, o) {
  var a, c, l = /* @__PURE__ */ new Map(), h = t.length, d = s.length, u = new Array(h), p;
  for (a = 0; a < h; ++a)
    (c = t[a]) && (u[a] = p = o.call(c, c.__data__, a, t) + "", l.has(p) ? r[a] = c : l.set(p, c));
  for (a = 0; a < d; ++a)
    p = o.call(i, s[a], a, s) + "", (c = l.get(p)) ? (n[a] = c, c.__data__ = s[a], l.delete(p)) : e[a] = new oi(i, s[a]);
  for (a = 0; a < h; ++a)
    (c = t[a]) && l.get(u[a]) === c && (r[a] = c);
}
function Ra(i) {
  return i.__data__;
}
function Ha(i, t) {
  if (!arguments.length) return Array.from(this, Ra);
  var e = t ? Ba : za, n = this._parents, r = this._groups;
  typeof i != "function" && (i = Fa(i));
  for (var s = r.length, o = new Array(s), a = new Array(s), c = new Array(s), l = 0; l < s; ++l) {
    var h = n[l], d = r[l], u = d.length, p = $a(i.call(h, h && h.__data__, l, n)), g = p.length, v = a[l] = new Array(g), y = o[l] = new Array(g), b = c[l] = new Array(u);
    e(h, d, v, y, b, p, t);
    for (var x = 0, S = 0, C, N; x < g; ++x)
      if (C = v[x]) {
        for (x >= S && (S = x + 1); !(N = y[S]) && ++S < g; ) ;
        C._next = N || null;
      }
  }
  return o = new wt(o, n), o._enter = a, o._exit = c, o;
}
function $a(i) {
  return typeof i == "object" && "length" in i ? i : Array.from(i);
}
function Ga() {
  return new wt(this._exit || this._groups.map(os), this._parents);
}
function qa(i, t, e) {
  var n = this.enter(), r = this, s = this.exit();
  return typeof i == "function" ? (n = i(n), n && (n = n.selection())) : n = n.append(i + ""), t != null && (r = t(r), r && (r = r.selection())), e == null ? s.remove() : e(s), n && r ? n.merge(r).order() : r;
}
function Va(i) {
  for (var t = i.selection ? i.selection() : i, e = this._groups, n = t._groups, r = e.length, s = n.length, o = Math.min(r, s), a = new Array(r), c = 0; c < o; ++c)
    for (var l = e[c], h = n[c], d = l.length, u = a[c] = new Array(d), p, g = 0; g < d; ++g)
      (p = l[g] || h[g]) && (u[g] = p);
  for (; c < r; ++c)
    a[c] = e[c];
  return new wt(a, this._parents);
}
function Ua() {
  for (var i = this._groups, t = -1, e = i.length; ++t < e; )
    for (var n = i[t], r = n.length - 1, s = n[r], o; --r >= 0; )
      (o = n[r]) && (s && o.compareDocumentPosition(s) ^ 4 && s.parentNode.insertBefore(o, s), s = o);
  return this;
}
function ja(i) {
  i || (i = Ya);
  function t(d, u) {
    return d && u ? i(d.__data__, u.__data__) : !d - !u;
  }
  for (var e = this._groups, n = e.length, r = new Array(n), s = 0; s < n; ++s) {
    for (var o = e[s], a = o.length, c = r[s] = new Array(a), l, h = 0; h < a; ++h)
      (l = o[h]) && (c[h] = l);
    c.sort(t);
  }
  return new wt(r, this._parents).order();
}
function Ya(i, t) {
  return i < t ? -1 : i > t ? 1 : i >= t ? 0 : NaN;
}
function Xa() {
  var i = arguments[0];
  return arguments[0] = this, i.apply(null, arguments), this;
}
function Wa() {
  return Array.from(this);
}
function Ka() {
  for (var i = this._groups, t = 0, e = i.length; t < e; ++t)
    for (var n = i[t], r = 0, s = n.length; r < s; ++r) {
      var o = n[r];
      if (o) return o;
    }
  return null;
}
function Za() {
  let i = 0;
  for (const t of this) ++i;
  return i;
}
function Qa() {
  return !this.node();
}
function Ja(i) {
  for (var t = this._groups, e = 0, n = t.length; e < n; ++e)
    for (var r = t[e], s = 0, o = r.length, a; s < o; ++s)
      (a = r[s]) && i.call(a, a.__data__, s, r);
  return this;
}
function tl(i) {
  return function() {
    this.removeAttribute(i);
  };
}
function el(i) {
  return function() {
    this.removeAttributeNS(i.space, i.local);
  };
}
function il(i, t) {
  return function() {
    this.setAttribute(i, t);
  };
}
function nl(i, t) {
  return function() {
    this.setAttributeNS(i.space, i.local, t);
  };
}
function rl(i, t) {
  return function() {
    var e = t.apply(this, arguments);
    e == null ? this.removeAttribute(i) : this.setAttribute(i, e);
  };
}
function sl(i, t) {
  return function() {
    var e = t.apply(this, arguments);
    e == null ? this.removeAttributeNS(i.space, i.local) : this.setAttributeNS(i.space, i.local, e);
  };
}
function ol(i, t) {
  var e = vi(i);
  if (arguments.length < 2) {
    var n = this.node();
    return e.local ? n.getAttributeNS(e.space, e.local) : n.getAttribute(e);
  }
  return this.each((t == null ? e.local ? el : tl : typeof t == "function" ? e.local ? sl : rl : e.local ? nl : il)(e, t));
}
function as(i) {
  return i.ownerDocument && i.ownerDocument.defaultView || i.document && i || i.defaultView;
}
function al(i) {
  return function() {
    this.style.removeProperty(i);
  };
}
function ll(i, t, e) {
  return function() {
    this.style.setProperty(i, t, e);
  };
}
function cl(i, t, e) {
  return function() {
    var n = t.apply(this, arguments);
    n == null ? this.style.removeProperty(i) : this.style.setProperty(i, n, e);
  };
}
function hl(i, t, e) {
  return arguments.length > 1 ? this.each((t == null ? al : typeof t == "function" ? cl : ll)(i, t, e ?? "")) : oe(this.node(), i);
}
function oe(i, t) {
  return i.style.getPropertyValue(t) || as(i).getComputedStyle(i, null).getPropertyValue(t);
}
function dl(i) {
  return function() {
    delete this[i];
  };
}
function ul(i, t) {
  return function() {
    this[i] = t;
  };
}
function pl(i, t) {
  return function() {
    var e = t.apply(this, arguments);
    e == null ? delete this[i] : this[i] = e;
  };
}
function fl(i, t) {
  return arguments.length > 1 ? this.each((t == null ? dl : typeof t == "function" ? pl : ul)(i, t)) : this.node()[i];
}
function ls(i) {
  return i.trim().split(/^|\s+/);
}
function En(i) {
  return i.classList || new cs(i);
}
function cs(i) {
  this._node = i, this._names = ls(i.getAttribute("class") || "");
}
cs.prototype = {
  add: function(i) {
    var t = this._names.indexOf(i);
    t < 0 && (this._names.push(i), this._node.setAttribute("class", this._names.join(" ")));
  },
  remove: function(i) {
    var t = this._names.indexOf(i);
    t >= 0 && (this._names.splice(t, 1), this._node.setAttribute("class", this._names.join(" ")));
  },
  contains: function(i) {
    return this._names.indexOf(i) >= 0;
  }
};
function hs(i, t) {
  for (var e = En(i), n = -1, r = t.length; ++n < r; ) e.add(t[n]);
}
function ds(i, t) {
  for (var e = En(i), n = -1, r = t.length; ++n < r; ) e.remove(t[n]);
}
function gl(i) {
  return function() {
    hs(this, i);
  };
}
function ml(i) {
  return function() {
    ds(this, i);
  };
}
function vl(i, t) {
  return function() {
    (t.apply(this, arguments) ? hs : ds)(this, i);
  };
}
function yl(i, t) {
  var e = ls(i + "");
  if (arguments.length < 2) {
    for (var n = En(this.node()), r = -1, s = e.length; ++r < s; ) if (!n.contains(e[r])) return !1;
    return !0;
  }
  return this.each((typeof t == "function" ? vl : t ? gl : ml)(e, t));
}
function bl() {
  this.textContent = "";
}
function wl(i) {
  return function() {
    this.textContent = i;
  };
}
function xl(i) {
  return function() {
    var t = i.apply(this, arguments);
    this.textContent = t ?? "";
  };
}
function Cl(i) {
  return arguments.length ? this.each(i == null ? bl : (typeof i == "function" ? xl : wl)(i)) : this.node().textContent;
}
function Ml() {
  this.innerHTML = "";
}
function El(i) {
  return function() {
    this.innerHTML = i;
  };
}
function Sl(i) {
  return function() {
    var t = i.apply(this, arguments);
    this.innerHTML = t ?? "";
  };
}
function _l(i) {
  return arguments.length ? this.each(i == null ? Ml : (typeof i == "function" ? Sl : El)(i)) : this.node().innerHTML;
}
function kl() {
  this.nextSibling && this.parentNode.appendChild(this);
}
function Nl() {
  return this.each(kl);
}
function Al() {
  this.previousSibling && this.parentNode.insertBefore(this, this.parentNode.firstChild);
}
function Il() {
  return this.each(Al);
}
function Ll(i) {
  var t = typeof i == "function" ? i : is(i);
  return this.select(function() {
    return this.appendChild(t.apply(this, arguments));
  });
}
function Ol() {
  return null;
}
function Tl(i, t) {
  var e = typeof i == "function" ? i : is(i), n = t == null ? Ol : typeof t == "function" ? t : Mn(t);
  return this.select(function() {
    return this.insertBefore(e.apply(this, arguments), n.apply(this, arguments) || null);
  });
}
function Pl() {
  var i = this.parentNode;
  i && i.removeChild(this);
}
function Dl() {
  return this.each(Pl);
}
function Fl() {
  var i = this.cloneNode(!1), t = this.parentNode;
  return t ? t.insertBefore(i, this.nextSibling) : i;
}
function zl() {
  var i = this.cloneNode(!0), t = this.parentNode;
  return t ? t.insertBefore(i, this.nextSibling) : i;
}
function Bl(i) {
  return this.select(i ? zl : Fl);
}
function Rl(i) {
  return arguments.length ? this.property("__data__", i) : this.node().__data__;
}
function Hl(i) {
  return function(t) {
    i.call(this, t, this.__data__);
  };
}
function $l(i) {
  return i.trim().split(/^|\s+/).map(function(t) {
    var e = "", n = t.indexOf(".");
    return n >= 0 && (e = t.slice(n + 1), t = t.slice(0, n)), { type: t, name: e };
  });
}
function Gl(i) {
  return function() {
    var t = this.__on;
    if (t) {
      for (var e = 0, n = -1, r = t.length, s; e < r; ++e)
        s = t[e], (!i.type || s.type === i.type) && s.name === i.name ? this.removeEventListener(s.type, s.listener, s.options) : t[++n] = s;
      ++n ? t.length = n : delete this.__on;
    }
  };
}
function ql(i, t, e) {
  return function() {
    var n = this.__on, r, s = Hl(t);
    if (n) {
      for (var o = 0, a = n.length; o < a; ++o)
        if ((r = n[o]).type === i.type && r.name === i.name) {
          this.removeEventListener(r.type, r.listener, r.options), this.addEventListener(r.type, r.listener = s, r.options = e), r.value = t;
          return;
        }
    }
    this.addEventListener(i.type, s, e), r = { type: i.type, name: i.name, value: t, listener: s, options: e }, n ? n.push(r) : this.__on = [r];
  };
}
function Vl(i, t, e) {
  var n = $l(i + ""), r, s = n.length, o;
  if (arguments.length < 2) {
    var a = this.node().__on;
    if (a) {
      for (var c = 0, l = a.length, h; c < l; ++c)
        for (r = 0, h = a[c]; r < s; ++r)
          if ((o = n[r]).type === h.type && o.name === h.name)
            return h.value;
    }
    return;
  }
  for (a = t ? ql : Gl, r = 0; r < s; ++r) this.each(a(n[r], t, e));
  return this;
}
function us(i, t, e) {
  var n = as(i), r = n.CustomEvent;
  typeof r == "function" ? r = new r(t, e) : (r = n.document.createEvent("Event"), e ? (r.initEvent(t, e.bubbles, e.cancelable), r.detail = e.detail) : r.initEvent(t, !1, !1)), i.dispatchEvent(r);
}
function Ul(i, t) {
  return function() {
    return us(this, i, t);
  };
}
function jl(i, t) {
  return function() {
    return us(this, i, t.apply(this, arguments));
  };
}
function Yl(i, t) {
  return this.each((typeof t == "function" ? jl : Ul)(i, t));
}
function* Xl() {
  for (var i = this._groups, t = 0, e = i.length; t < e; ++t)
    for (var n = i[t], r = 0, s = n.length, o; r < s; ++r)
      (o = n[r]) && (yield o);
}
var ps = [null];
function wt(i, t) {
  this._groups = i, this._parents = t;
}
function ce() {
  return new wt([[document.documentElement]], ps);
}
function Wl() {
  return this;
}
wt.prototype = ce.prototype = {
  constructor: wt,
  select: xa,
  selectAll: Sa,
  selectChild: Aa,
  selectChildren: Ta,
  filter: Pa,
  data: Ha,
  enter: Da,
  exit: Ga,
  join: qa,
  merge: Va,
  selection: Wl,
  order: Ua,
  sort: ja,
  call: Xa,
  nodes: Wa,
  node: Ka,
  size: Za,
  empty: Qa,
  each: Ja,
  attr: ol,
  style: hl,
  property: fl,
  classed: yl,
  text: Cl,
  html: _l,
  raise: Nl,
  lower: Il,
  append: Ll,
  insert: Tl,
  remove: Dl,
  clone: Bl,
  datum: Rl,
  on: Vl,
  dispatch: Yl,
  [Symbol.iterator]: Xl
};
function tt(i) {
  return typeof i == "string" ? new wt([[document.querySelector(i)]], [document.documentElement]) : new wt([[i]], ps);
}
function Kl(i) {
  let t;
  for (; t = i.sourceEvent; ) i = t;
  return i;
}
function Pt(i, t) {
  if (i = Kl(i), t === void 0 && (t = i.currentTarget), t) {
    var e = t.ownerSVGElement || t;
    if (e.createSVGPoint) {
      var n = e.createSVGPoint();
      return n.x = i.clientX, n.y = i.clientY, n = n.matrixTransform(t.getScreenCTM().inverse()), [n.x, n.y];
    }
    if (t.getBoundingClientRect) {
      var r = t.getBoundingClientRect();
      return [i.clientX - r.left - t.clientLeft, i.clientY - r.top - t.clientTop];
    }
  }
  return [i.pageX, i.pageY];
}
var Zl = { value: () => {
} };
function Ne() {
  for (var i = 0, t = arguments.length, e = {}, n; i < t; ++i) {
    if (!(n = arguments[i] + "") || n in e || /[\s.]/.test(n)) throw new Error("illegal type: " + n);
    e[n] = [];
  }
  return new Ze(e);
}
function Ze(i) {
  this._ = i;
}
function Ql(i, t) {
  return i.trim().split(/^|\s+/).map(function(e) {
    var n = "", r = e.indexOf(".");
    if (r >= 0 && (n = e.slice(r + 1), e = e.slice(0, r)), e && !t.hasOwnProperty(e)) throw new Error("unknown type: " + e);
    return { type: e, name: n };
  });
}
Ze.prototype = Ne.prototype = {
  constructor: Ze,
  on: function(i, t) {
    var e = this._, n = Ql(i + "", e), r, s = -1, o = n.length;
    if (arguments.length < 2) {
      for (; ++s < o; ) if ((r = (i = n[s]).type) && (r = Jl(e[r], i.name))) return r;
      return;
    }
    if (t != null && typeof t != "function") throw new Error("invalid callback: " + t);
    for (; ++s < o; )
      if (r = (i = n[s]).type) e[r] = nr(e[r], i.name, t);
      else if (t == null) for (r in e) e[r] = nr(e[r], i.name, null);
    return this;
  },
  copy: function() {
    var i = {}, t = this._;
    for (var e in t) i[e] = t[e].slice();
    return new Ze(i);
  },
  call: function(i, t) {
    if ((r = arguments.length - 2) > 0) for (var e = new Array(r), n = 0, r, s; n < r; ++n) e[n] = arguments[n + 2];
    if (!this._.hasOwnProperty(i)) throw new Error("unknown type: " + i);
    for (s = this._[i], n = 0, r = s.length; n < r; ++n) s[n].value.apply(t, e);
  },
  apply: function(i, t, e) {
    if (!this._.hasOwnProperty(i)) throw new Error("unknown type: " + i);
    for (var n = this._[i], r = 0, s = n.length; r < s; ++r) n[r].value.apply(t, e);
  }
};
function Jl(i, t) {
  for (var e = 0, n = i.length, r; e < n; ++e)
    if ((r = i[e]).name === t)
      return r.value;
}
function nr(i, t, e) {
  for (var n = 0, r = i.length; n < r; ++n)
    if (i[n].name === t) {
      i[n] = Zl, i = i.slice(0, n).concat(i.slice(n + 1));
      break;
    }
  return e != null && i.push({ name: t, value: e }), i;
}
var ae = 0, ge = 0, pe = 0, fs = 1e3, ai, me, li = 0, Kt = 0, yi = 0, xe = typeof performance == "object" && performance.now ? performance : Date, gs = typeof window == "object" && window.requestAnimationFrame ? window.requestAnimationFrame.bind(window) : function(i) {
  setTimeout(i, 17);
};
function Sn() {
  return Kt || (gs(tc), Kt = xe.now() + yi);
}
function tc() {
  Kt = 0;
}
function ci() {
  this._call = this._time = this._next = null;
}
ci.prototype = _n.prototype = {
  constructor: ci,
  restart: function(i, t, e) {
    if (typeof i != "function") throw new TypeError("callback is not a function");
    e = (e == null ? Sn() : +e) + (t == null ? 0 : +t), !this._next && me !== this && (me ? me._next = this : ai = this, me = this), this._call = i, this._time = e, an();
  },
  stop: function() {
    this._call && (this._call = null, this._time = 1 / 0, an());
  }
};
function _n(i, t, e) {
  var n = new ci();
  return n.restart(i, t, e), n;
}
function ec() {
  Sn(), ++ae;
  for (var i = ai, t; i; )
    (t = Kt - i._time) >= 0 && i._call.call(void 0, t), i = i._next;
  --ae;
}
function rr() {
  Kt = (li = xe.now()) + yi, ae = ge = 0;
  try {
    ec();
  } finally {
    ae = 0, nc(), Kt = 0;
  }
}
function ic() {
  var i = xe.now(), t = i - li;
  t > fs && (yi -= t, li = i);
}
function nc() {
  for (var i, t = ai, e, n = 1 / 0; t; )
    t._call ? (n > t._time && (n = t._time), i = t, t = t._next) : (e = t._next, t._next = null, t = i ? i._next = e : ai = e);
  me = i, an(n);
}
function an(i) {
  if (!ae) {
    ge && (ge = clearTimeout(ge));
    var t = i - Kt;
    t > 24 ? (i < 1 / 0 && (ge = setTimeout(rr, i - xe.now() - yi)), pe && (pe = clearInterval(pe))) : (pe || (li = xe.now(), pe = setInterval(ic, fs)), ae = 1, gs(rr));
  }
}
function sr(i, t, e) {
  var n = new ci();
  return t = t == null ? 0 : +t, n.restart((r) => {
    n.stop(), i(r + t);
  }, t, e), n;
}
var rc = Ne("start", "end", "cancel", "interrupt"), sc = [], ms = 0, or = 1, ln = 2, Qe = 3, ar = 4, cn = 5, Je = 6;
function bi(i, t, e, n, r, s) {
  var o = i.__transition;
  if (!o) i.__transition = {};
  else if (e in o) return;
  oc(i, e, {
    name: t,
    index: n,
    // For context during callback.
    group: r,
    // For context during callback.
    on: rc,
    tween: sc,
    time: s.time,
    delay: s.delay,
    duration: s.duration,
    ease: s.ease,
    timer: null,
    state: ms
  });
}
function kn(i, t) {
  var e = kt(i, t);
  if (e.state > ms) throw new Error("too late; already scheduled");
  return e;
}
function Lt(i, t) {
  var e = kt(i, t);
  if (e.state > Qe) throw new Error("too late; already running");
  return e;
}
function kt(i, t) {
  var e = i.__transition;
  if (!e || !(e = e[t])) throw new Error("transition not found");
  return e;
}
function oc(i, t, e) {
  var n = i.__transition, r;
  n[t] = e, e.timer = _n(s, 0, e.time);
  function s(l) {
    e.state = or, e.timer.restart(o, e.delay, e.time), e.delay <= l && o(l - e.delay);
  }
  function o(l) {
    var h, d, u, p;
    if (e.state !== or) return c();
    for (h in n)
      if (p = n[h], p.name === e.name) {
        if (p.state === Qe) return sr(o);
        p.state === ar ? (p.state = Je, p.timer.stop(), p.on.call("interrupt", i, i.__data__, p.index, p.group), delete n[h]) : +h < t && (p.state = Je, p.timer.stop(), p.on.call("cancel", i, i.__data__, p.index, p.group), delete n[h]);
      }
    if (sr(function() {
      e.state === Qe && (e.state = ar, e.timer.restart(a, e.delay, e.time), a(l));
    }), e.state = ln, e.on.call("start", i, i.__data__, e.index, e.group), e.state === ln) {
      for (e.state = Qe, r = new Array(u = e.tween.length), h = 0, d = -1; h < u; ++h)
        (p = e.tween[h].value.call(i, i.__data__, e.index, e.group)) && (r[++d] = p);
      r.length = d + 1;
    }
  }
  function a(l) {
    for (var h = l < e.duration ? e.ease.call(null, l / e.duration) : (e.timer.restart(c), e.state = cn, 1), d = -1, u = r.length; ++d < u; )
      r[d].call(i, h);
    e.state === cn && (e.on.call("end", i, i.__data__, e.index, e.group), c());
  }
  function c() {
    e.state = Je, e.timer.stop(), delete n[t];
    for (var l in n) return;
    delete i.__transition;
  }
}
function ti(i, t) {
  var e = i.__transition, n, r, s = !0, o;
  if (e) {
    t = t == null ? null : t + "";
    for (o in e) {
      if ((n = e[o]).name !== t) {
        s = !1;
        continue;
      }
      r = n.state > ln && n.state < cn, n.state = Je, n.timer.stop(), n.on.call(r ? "interrupt" : "cancel", i, i.__data__, n.index, n.group), delete e[o];
    }
    s && delete i.__transition;
  }
}
function ac(i) {
  return this.each(function() {
    ti(this, i);
  });
}
function Nn(i, t, e) {
  i.prototype = t.prototype = e, e.constructor = i;
}
function vs(i, t) {
  var e = Object.create(i.prototype);
  for (var n in t) e[n] = t[n];
  return e;
}
function Ae() {
}
var Ce = 0.7, hi = 1 / Ce, ie = "\\s*([+-]?\\d+)\\s*", Me = "\\s*([+-]?(?:\\d*\\.)?\\d+(?:[eE][+-]?\\d+)?)\\s*", It = "\\s*([+-]?(?:\\d*\\.)?\\d+(?:[eE][+-]?\\d+)?)%\\s*", lc = /^#([0-9a-f]{3,8})$/, cc = new RegExp(`^rgb\\(${ie},${ie},${ie}\\)$`), hc = new RegExp(`^rgb\\(${It},${It},${It}\\)$`), dc = new RegExp(`^rgba\\(${ie},${ie},${ie},${Me}\\)$`), uc = new RegExp(`^rgba\\(${It},${It},${It},${Me}\\)$`), pc = new RegExp(`^hsl\\(${Me},${It},${It}\\)$`), fc = new RegExp(`^hsla\\(${Me},${It},${It},${Me}\\)$`), lr = {
  aliceblue: 15792383,
  antiquewhite: 16444375,
  aqua: 65535,
  aquamarine: 8388564,
  azure: 15794175,
  beige: 16119260,
  bisque: 16770244,
  black: 0,
  blanchedalmond: 16772045,
  blue: 255,
  blueviolet: 9055202,
  brown: 10824234,
  burlywood: 14596231,
  cadetblue: 6266528,
  chartreuse: 8388352,
  chocolate: 13789470,
  coral: 16744272,
  cornflowerblue: 6591981,
  cornsilk: 16775388,
  crimson: 14423100,
  cyan: 65535,
  darkblue: 139,
  darkcyan: 35723,
  darkgoldenrod: 12092939,
  darkgray: 11119017,
  darkgreen: 25600,
  darkgrey: 11119017,
  darkkhaki: 12433259,
  darkmagenta: 9109643,
  darkolivegreen: 5597999,
  darkorange: 16747520,
  darkorchid: 10040012,
  darkred: 9109504,
  darksalmon: 15308410,
  darkseagreen: 9419919,
  darkslateblue: 4734347,
  darkslategray: 3100495,
  darkslategrey: 3100495,
  darkturquoise: 52945,
  darkviolet: 9699539,
  deeppink: 16716947,
  deepskyblue: 49151,
  dimgray: 6908265,
  dimgrey: 6908265,
  dodgerblue: 2003199,
  firebrick: 11674146,
  floralwhite: 16775920,
  forestgreen: 2263842,
  fuchsia: 16711935,
  gainsboro: 14474460,
  ghostwhite: 16316671,
  gold: 16766720,
  goldenrod: 14329120,
  gray: 8421504,
  green: 32768,
  greenyellow: 11403055,
  grey: 8421504,
  honeydew: 15794160,
  hotpink: 16738740,
  indianred: 13458524,
  indigo: 4915330,
  ivory: 16777200,
  khaki: 15787660,
  lavender: 15132410,
  lavenderblush: 16773365,
  lawngreen: 8190976,
  lemonchiffon: 16775885,
  lightblue: 11393254,
  lightcoral: 15761536,
  lightcyan: 14745599,
  lightgoldenrodyellow: 16448210,
  lightgray: 13882323,
  lightgreen: 9498256,
  lightgrey: 13882323,
  lightpink: 16758465,
  lightsalmon: 16752762,
  lightseagreen: 2142890,
  lightskyblue: 8900346,
  lightslategray: 7833753,
  lightslategrey: 7833753,
  lightsteelblue: 11584734,
  lightyellow: 16777184,
  lime: 65280,
  limegreen: 3329330,
  linen: 16445670,
  magenta: 16711935,
  maroon: 8388608,
  mediumaquamarine: 6737322,
  mediumblue: 205,
  mediumorchid: 12211667,
  mediumpurple: 9662683,
  mediumseagreen: 3978097,
  mediumslateblue: 8087790,
  mediumspringgreen: 64154,
  mediumturquoise: 4772300,
  mediumvioletred: 13047173,
  midnightblue: 1644912,
  mintcream: 16121850,
  mistyrose: 16770273,
  moccasin: 16770229,
  navajowhite: 16768685,
  navy: 128,
  oldlace: 16643558,
  olive: 8421376,
  olivedrab: 7048739,
  orange: 16753920,
  orangered: 16729344,
  orchid: 14315734,
  palegoldenrod: 15657130,
  palegreen: 10025880,
  paleturquoise: 11529966,
  palevioletred: 14381203,
  papayawhip: 16773077,
  peachpuff: 16767673,
  peru: 13468991,
  pink: 16761035,
  plum: 14524637,
  powderblue: 11591910,
  purple: 8388736,
  rebeccapurple: 6697881,
  red: 16711680,
  rosybrown: 12357519,
  royalblue: 4286945,
  saddlebrown: 9127187,
  salmon: 16416882,
  sandybrown: 16032864,
  seagreen: 3050327,
  seashell: 16774638,
  sienna: 10506797,
  silver: 12632256,
  skyblue: 8900331,
  slateblue: 6970061,
  slategray: 7372944,
  slategrey: 7372944,
  snow: 16775930,
  springgreen: 65407,
  steelblue: 4620980,
  tan: 13808780,
  teal: 32896,
  thistle: 14204888,
  tomato: 16737095,
  turquoise: 4251856,
  violet: 15631086,
  wheat: 16113331,
  white: 16777215,
  whitesmoke: 16119285,
  yellow: 16776960,
  yellowgreen: 10145074
};
Nn(Ae, Ee, {
  copy(i) {
    return Object.assign(new this.constructor(), this, i);
  },
  displayable() {
    return this.rgb().displayable();
  },
  hex: cr,
  // Deprecated! Use color.formatHex.
  formatHex: cr,
  formatHex8: gc,
  formatHsl: mc,
  formatRgb: hr,
  toString: hr
});
function cr() {
  return this.rgb().formatHex();
}
function gc() {
  return this.rgb().formatHex8();
}
function mc() {
  return ys(this).formatHsl();
}
function hr() {
  return this.rgb().formatRgb();
}
function Ee(i) {
  var t, e;
  return i = (i + "").trim().toLowerCase(), (t = lc.exec(i)) ? (e = t[1].length, t = parseInt(t[1], 16), e === 6 ? dr(t) : e === 3 ? new gt(t >> 8 & 15 | t >> 4 & 240, t >> 4 & 15 | t & 240, (t & 15) << 4 | t & 15, 1) : e === 8 ? Be(t >> 24 & 255, t >> 16 & 255, t >> 8 & 255, (t & 255) / 255) : e === 4 ? Be(t >> 12 & 15 | t >> 8 & 240, t >> 8 & 15 | t >> 4 & 240, t >> 4 & 15 | t & 240, ((t & 15) << 4 | t & 15) / 255) : null) : (t = cc.exec(i)) ? new gt(t[1], t[2], t[3], 1) : (t = hc.exec(i)) ? new gt(t[1] * 255 / 100, t[2] * 255 / 100, t[3] * 255 / 100, 1) : (t = dc.exec(i)) ? Be(t[1], t[2], t[3], t[4]) : (t = uc.exec(i)) ? Be(t[1] * 255 / 100, t[2] * 255 / 100, t[3] * 255 / 100, t[4]) : (t = pc.exec(i)) ? fr(t[1], t[2] / 100, t[3] / 100, 1) : (t = fc.exec(i)) ? fr(t[1], t[2] / 100, t[3] / 100, t[4]) : lr.hasOwnProperty(i) ? dr(lr[i]) : i === "transparent" ? new gt(NaN, NaN, NaN, 0) : null;
}
function dr(i) {
  return new gt(i >> 16 & 255, i >> 8 & 255, i & 255, 1);
}
function Be(i, t, e, n) {
  return n <= 0 && (i = t = e = NaN), new gt(i, t, e, n);
}
function vc(i) {
  return i instanceof Ae || (i = Ee(i)), i ? (i = i.rgb(), new gt(i.r, i.g, i.b, i.opacity)) : new gt();
}
function hn(i, t, e, n) {
  return arguments.length === 1 ? vc(i) : new gt(i, t, e, n ?? 1);
}
function gt(i, t, e, n) {
  this.r = +i, this.g = +t, this.b = +e, this.opacity = +n;
}
Nn(gt, hn, vs(Ae, {
  brighter(i) {
    return i = i == null ? hi : Math.pow(hi, i), new gt(this.r * i, this.g * i, this.b * i, this.opacity);
  },
  darker(i) {
    return i = i == null ? Ce : Math.pow(Ce, i), new gt(this.r * i, this.g * i, this.b * i, this.opacity);
  },
  rgb() {
    return this;
  },
  clamp() {
    return new gt(Xt(this.r), Xt(this.g), Xt(this.b), di(this.opacity));
  },
  displayable() {
    return -0.5 <= this.r && this.r < 255.5 && -0.5 <= this.g && this.g < 255.5 && -0.5 <= this.b && this.b < 255.5 && 0 <= this.opacity && this.opacity <= 1;
  },
  hex: ur,
  // Deprecated! Use color.formatHex.
  formatHex: ur,
  formatHex8: yc,
  formatRgb: pr,
  toString: pr
}));
function ur() {
  return `#${Yt(this.r)}${Yt(this.g)}${Yt(this.b)}`;
}
function yc() {
  return `#${Yt(this.r)}${Yt(this.g)}${Yt(this.b)}${Yt((isNaN(this.opacity) ? 1 : this.opacity) * 255)}`;
}
function pr() {
  const i = di(this.opacity);
  return `${i === 1 ? "rgb(" : "rgba("}${Xt(this.r)}, ${Xt(this.g)}, ${Xt(this.b)}${i === 1 ? ")" : `, ${i})`}`;
}
function di(i) {
  return isNaN(i) ? 1 : Math.max(0, Math.min(1, i));
}
function Xt(i) {
  return Math.max(0, Math.min(255, Math.round(i) || 0));
}
function Yt(i) {
  return i = Xt(i), (i < 16 ? "0" : "") + i.toString(16);
}
function fr(i, t, e, n) {
  return n <= 0 ? i = t = e = NaN : e <= 0 || e >= 1 ? i = t = NaN : t <= 0 && (i = NaN), new Et(i, t, e, n);
}
function ys(i) {
  if (i instanceof Et) return new Et(i.h, i.s, i.l, i.opacity);
  if (i instanceof Ae || (i = Ee(i)), !i) return new Et();
  if (i instanceof Et) return i;
  i = i.rgb();
  var t = i.r / 255, e = i.g / 255, n = i.b / 255, r = Math.min(t, e, n), s = Math.max(t, e, n), o = NaN, a = s - r, c = (s + r) / 2;
  return a ? (t === s ? o = (e - n) / a + (e < n) * 6 : e === s ? o = (n - t) / a + 2 : o = (t - e) / a + 4, a /= c < 0.5 ? s + r : 2 - s - r, o *= 60) : a = c > 0 && c < 1 ? 0 : o, new Et(o, a, c, i.opacity);
}
function bc(i, t, e, n) {
  return arguments.length === 1 ? ys(i) : new Et(i, t, e, n ?? 1);
}
function Et(i, t, e, n) {
  this.h = +i, this.s = +t, this.l = +e, this.opacity = +n;
}
Nn(Et, bc, vs(Ae, {
  brighter(i) {
    return i = i == null ? hi : Math.pow(hi, i), new Et(this.h, this.s, this.l * i, this.opacity);
  },
  darker(i) {
    return i = i == null ? Ce : Math.pow(Ce, i), new Et(this.h, this.s, this.l * i, this.opacity);
  },
  rgb() {
    var i = this.h % 360 + (this.h < 0) * 360, t = isNaN(i) || isNaN(this.s) ? 0 : this.s, e = this.l, n = e + (e < 0.5 ? e : 1 - e) * t, r = 2 * e - n;
    return new gt(
      Fi(i >= 240 ? i - 240 : i + 120, r, n),
      Fi(i, r, n),
      Fi(i < 120 ? i + 240 : i - 120, r, n),
      this.opacity
    );
  },
  clamp() {
    return new Et(gr(this.h), Re(this.s), Re(this.l), di(this.opacity));
  },
  displayable() {
    return (0 <= this.s && this.s <= 1 || isNaN(this.s)) && 0 <= this.l && this.l <= 1 && 0 <= this.opacity && this.opacity <= 1;
  },
  formatHsl() {
    const i = di(this.opacity);
    return `${i === 1 ? "hsl(" : "hsla("}${gr(this.h)}, ${Re(this.s) * 100}%, ${Re(this.l) * 100}%${i === 1 ? ")" : `, ${i})`}`;
  }
}));
function gr(i) {
  return i = (i || 0) % 360, i < 0 ? i + 360 : i;
}
function Re(i) {
  return Math.max(0, Math.min(1, i || 0));
}
function Fi(i, t, e) {
  return (i < 60 ? t + (e - t) * i / 60 : i < 180 ? e : i < 240 ? t + (e - t) * (240 - i) / 60 : t) * 255;
}
const bs = (i) => () => i;
function wc(i, t) {
  return function(e) {
    return i + e * t;
  };
}
function xc(i, t, e) {
  return i = Math.pow(i, e), t = Math.pow(t, e) - i, e = 1 / e, function(n) {
    return Math.pow(i + n * t, e);
  };
}
function Cc(i) {
  return (i = +i) == 1 ? ws : function(t, e) {
    return e - t ? xc(t, e, i) : bs(isNaN(t) ? e : t);
  };
}
function ws(i, t) {
  var e = t - i;
  return e ? wc(i, e) : bs(isNaN(i) ? t : i);
}
const mr = (function i(t) {
  var e = Cc(t);
  function n(r, s) {
    var o = e((r = hn(r)).r, (s = hn(s)).r), a = e(r.g, s.g), c = e(r.b, s.b), l = ws(r.opacity, s.opacity);
    return function(h) {
      return r.r = o(h), r.g = a(h), r.b = c(h), r.opacity = l(h), r + "";
    };
  }
  return n.gamma = i, n;
})(1);
function Rt(i, t) {
  return i = +i, t = +t, function(e) {
    return i * (1 - e) + t * e;
  };
}
var dn = /[-+]?(?:\d+\.?\d*|\.?\d+)(?:[eE][-+]?\d+)?/g, zi = new RegExp(dn.source, "g");
function Mc(i) {
  return function() {
    return i;
  };
}
function Ec(i) {
  return function(t) {
    return i(t) + "";
  };
}
function Sc(i, t) {
  var e = dn.lastIndex = zi.lastIndex = 0, n, r, s, o = -1, a = [], c = [];
  for (i = i + "", t = t + ""; (n = dn.exec(i)) && (r = zi.exec(t)); )
    (s = r.index) > e && (s = t.slice(e, s), a[o] ? a[o] += s : a[++o] = s), (n = n[0]) === (r = r[0]) ? a[o] ? a[o] += r : a[++o] = r : (a[++o] = null, c.push({ i: o, x: Rt(n, r) })), e = zi.lastIndex;
  return e < t.length && (s = t.slice(e), a[o] ? a[o] += s : a[++o] = s), a.length < 2 ? c[0] ? Ec(c[0].x) : Mc(t) : (t = c.length, function(l) {
    for (var h = 0, d; h < t; ++h) a[(d = c[h]).i] = d.x(l);
    return a.join("");
  });
}
var vr = 180 / Math.PI, un = {
  translateX: 0,
  translateY: 0,
  rotate: 0,
  skewX: 0,
  scaleX: 1,
  scaleY: 1
};
function xs(i, t, e, n, r, s) {
  var o, a, c;
  return (o = Math.sqrt(i * i + t * t)) && (i /= o, t /= o), (c = i * e + t * n) && (e -= i * c, n -= t * c), (a = Math.sqrt(e * e + n * n)) && (e /= a, n /= a, c /= a), i * n < t * e && (i = -i, t = -t, c = -c, o = -o), {
    translateX: r,
    translateY: s,
    rotate: Math.atan2(t, i) * vr,
    skewX: Math.atan(c) * vr,
    scaleX: o,
    scaleY: a
  };
}
var He;
function _c(i) {
  const t = new (typeof DOMMatrix == "function" ? DOMMatrix : WebKitCSSMatrix)(i + "");
  return t.isIdentity ? un : xs(t.a, t.b, t.c, t.d, t.e, t.f);
}
function kc(i) {
  return i == null || (He || (He = document.createElementNS("http://www.w3.org/2000/svg", "g")), He.setAttribute("transform", i), !(i = He.transform.baseVal.consolidate())) ? un : (i = i.matrix, xs(i.a, i.b, i.c, i.d, i.e, i.f));
}
function Cs(i, t, e, n) {
  function r(l) {
    return l.length ? l.pop() + " " : "";
  }
  function s(l, h, d, u, p, g) {
    if (l !== d || h !== u) {
      var v = p.push("translate(", null, t, null, e);
      g.push({ i: v - 4, x: Rt(l, d) }, { i: v - 2, x: Rt(h, u) });
    } else (d || u) && p.push("translate(" + d + t + u + e);
  }
  function o(l, h, d, u) {
    l !== h ? (l - h > 180 ? h += 360 : h - l > 180 && (l += 360), u.push({ i: d.push(r(d) + "rotate(", null, n) - 2, x: Rt(l, h) })) : h && d.push(r(d) + "rotate(" + h + n);
  }
  function a(l, h, d, u) {
    l !== h ? u.push({ i: d.push(r(d) + "skewX(", null, n) - 2, x: Rt(l, h) }) : h && d.push(r(d) + "skewX(" + h + n);
  }
  function c(l, h, d, u, p, g) {
    if (l !== d || h !== u) {
      var v = p.push(r(p) + "scale(", null, ",", null, ")");
      g.push({ i: v - 4, x: Rt(l, d) }, { i: v - 2, x: Rt(h, u) });
    } else (d !== 1 || u !== 1) && p.push(r(p) + "scale(" + d + "," + u + ")");
  }
  return function(l, h) {
    var d = [], u = [];
    return l = i(l), h = i(h), s(l.translateX, l.translateY, h.translateX, h.translateY, d, u), o(l.rotate, h.rotate, d, u), a(l.skewX, h.skewX, d, u), c(l.scaleX, l.scaleY, h.scaleX, h.scaleY, d, u), l = h = null, function(p) {
      for (var g = -1, v = u.length, y; ++g < v; ) d[(y = u[g]).i] = y.x(p);
      return d.join("");
    };
  };
}
var Nc = Cs(_c, "px, ", "px)", "deg)"), Ac = Cs(kc, ", ", ")", ")"), Ic = 1e-12;
function yr(i) {
  return ((i = Math.exp(i)) + 1 / i) / 2;
}
function Lc(i) {
  return ((i = Math.exp(i)) - 1 / i) / 2;
}
function Oc(i) {
  return ((i = Math.exp(2 * i)) - 1) / (i + 1);
}
const Tc = (function i(t, e, n) {
  function r(s, o) {
    var a = s[0], c = s[1], l = s[2], h = o[0], d = o[1], u = o[2], p = h - a, g = d - c, v = p * p + g * g, y, b;
    if (v < Ic)
      b = Math.log(u / l) / t, y = function(k) {
        return [
          a + k * p,
          c + k * g,
          l * Math.exp(t * k * b)
        ];
      };
    else {
      var x = Math.sqrt(v), S = (u * u - l * l + n * v) / (2 * l * e * x), C = (u * u - l * l - n * v) / (2 * u * e * x), N = Math.log(Math.sqrt(S * S + 1) - S), P = Math.log(Math.sqrt(C * C + 1) - C);
      b = (P - N) / t, y = function(k) {
        var A = k * b, I = yr(N), z = l / (e * x) * (I * Oc(t * A + N) - Lc(N));
        return [
          a + z * p,
          c + z * g,
          l * I / yr(t * A + N)
        ];
      };
    }
    return y.duration = b * 1e3 * t / Math.SQRT2, y;
  }
  return r.rho = function(s) {
    var o = Math.max(1e-3, +s), a = o * o, c = a * a;
    return i(o, a, c);
  }, r;
})(Math.SQRT2, 2, 4);
function Pc(i, t) {
  var e, n;
  return function() {
    var r = Lt(this, i), s = r.tween;
    if (s !== e) {
      n = e = s;
      for (var o = 0, a = n.length; o < a; ++o)
        if (n[o].name === t) {
          n = n.slice(), n.splice(o, 1);
          break;
        }
    }
    r.tween = n;
  };
}
function Dc(i, t, e) {
  var n, r;
  if (typeof e != "function") throw new Error();
  return function() {
    var s = Lt(this, i), o = s.tween;
    if (o !== n) {
      r = (n = o).slice();
      for (var a = { name: t, value: e }, c = 0, l = r.length; c < l; ++c)
        if (r[c].name === t) {
          r[c] = a;
          break;
        }
      c === l && r.push(a);
    }
    s.tween = r;
  };
}
function Fc(i, t) {
  var e = this._id;
  if (i += "", arguments.length < 2) {
    for (var n = kt(this.node(), e).tween, r = 0, s = n.length, o; r < s; ++r)
      if ((o = n[r]).name === i)
        return o.value;
    return null;
  }
  return this.each((t == null ? Pc : Dc)(e, i, t));
}
function An(i, t, e) {
  var n = i._id;
  return i.each(function() {
    var r = Lt(this, n);
    (r.value || (r.value = {}))[t] = e.apply(this, arguments);
  }), function(r) {
    return kt(r, n).value[t];
  };
}
function Ms(i, t) {
  var e;
  return (typeof t == "number" ? Rt : t instanceof Ee ? mr : (e = Ee(t)) ? (t = e, mr) : Sc)(i, t);
}
function zc(i) {
  return function() {
    this.removeAttribute(i);
  };
}
function Bc(i) {
  return function() {
    this.removeAttributeNS(i.space, i.local);
  };
}
function Rc(i, t, e) {
  var n, r = e + "", s;
  return function() {
    var o = this.getAttribute(i);
    return o === r ? null : o === n ? s : s = t(n = o, e);
  };
}
function Hc(i, t, e) {
  var n, r = e + "", s;
  return function() {
    var o = this.getAttributeNS(i.space, i.local);
    return o === r ? null : o === n ? s : s = t(n = o, e);
  };
}
function $c(i, t, e) {
  var n, r, s;
  return function() {
    var o, a = e(this), c;
    return a == null ? void this.removeAttribute(i) : (o = this.getAttribute(i), c = a + "", o === c ? null : o === n && c === r ? s : (r = c, s = t(n = o, a)));
  };
}
function Gc(i, t, e) {
  var n, r, s;
  return function() {
    var o, a = e(this), c;
    return a == null ? void this.removeAttributeNS(i.space, i.local) : (o = this.getAttributeNS(i.space, i.local), c = a + "", o === c ? null : o === n && c === r ? s : (r = c, s = t(n = o, a)));
  };
}
function qc(i, t) {
  var e = vi(i), n = e === "transform" ? Ac : Ms;
  return this.attrTween(i, typeof t == "function" ? (e.local ? Gc : $c)(e, n, An(this, "attr." + i, t)) : t == null ? (e.local ? Bc : zc)(e) : (e.local ? Hc : Rc)(e, n, t));
}
function Vc(i, t) {
  return function(e) {
    this.setAttribute(i, t.call(this, e));
  };
}
function Uc(i, t) {
  return function(e) {
    this.setAttributeNS(i.space, i.local, t.call(this, e));
  };
}
function jc(i, t) {
  var e, n;
  function r() {
    var s = t.apply(this, arguments);
    return s !== n && (e = (n = s) && Uc(i, s)), e;
  }
  return r._value = t, r;
}
function Yc(i, t) {
  var e, n;
  function r() {
    var s = t.apply(this, arguments);
    return s !== n && (e = (n = s) && Vc(i, s)), e;
  }
  return r._value = t, r;
}
function Xc(i, t) {
  var e = "attr." + i;
  if (arguments.length < 2) return (e = this.tween(e)) && e._value;
  if (t == null) return this.tween(e, null);
  if (typeof t != "function") throw new Error();
  var n = vi(i);
  return this.tween(e, (n.local ? jc : Yc)(n, t));
}
function Wc(i, t) {
  return function() {
    kn(this, i).delay = +t.apply(this, arguments);
  };
}
function Kc(i, t) {
  return t = +t, function() {
    kn(this, i).delay = t;
  };
}
function Zc(i) {
  var t = this._id;
  return arguments.length ? this.each((typeof i == "function" ? Wc : Kc)(t, i)) : kt(this.node(), t).delay;
}
function Qc(i, t) {
  return function() {
    Lt(this, i).duration = +t.apply(this, arguments);
  };
}
function Jc(i, t) {
  return t = +t, function() {
    Lt(this, i).duration = t;
  };
}
function th(i) {
  var t = this._id;
  return arguments.length ? this.each((typeof i == "function" ? Qc : Jc)(t, i)) : kt(this.node(), t).duration;
}
function eh(i, t) {
  if (typeof t != "function") throw new Error();
  return function() {
    Lt(this, i).ease = t;
  };
}
function ih(i) {
  var t = this._id;
  return arguments.length ? this.each(eh(t, i)) : kt(this.node(), t).ease;
}
function nh(i, t) {
  return function() {
    var e = t.apply(this, arguments);
    if (typeof e != "function") throw new Error();
    Lt(this, i).ease = e;
  };
}
function rh(i) {
  if (typeof i != "function") throw new Error();
  return this.each(nh(this._id, i));
}
function sh(i) {
  typeof i != "function" && (i = rs(i));
  for (var t = this._groups, e = t.length, n = new Array(e), r = 0; r < e; ++r)
    for (var s = t[r], o = s.length, a = n[r] = [], c, l = 0; l < o; ++l)
      (c = s[l]) && i.call(c, c.__data__, l, s) && a.push(c);
  return new Ft(n, this._parents, this._name, this._id);
}
function oh(i) {
  if (i._id !== this._id) throw new Error();
  for (var t = this._groups, e = i._groups, n = t.length, r = e.length, s = Math.min(n, r), o = new Array(n), a = 0; a < s; ++a)
    for (var c = t[a], l = e[a], h = c.length, d = o[a] = new Array(h), u, p = 0; p < h; ++p)
      (u = c[p] || l[p]) && (d[p] = u);
  for (; a < n; ++a)
    o[a] = t[a];
  return new Ft(o, this._parents, this._name, this._id);
}
function ah(i) {
  return (i + "").trim().split(/^|\s+/).every(function(t) {
    var e = t.indexOf(".");
    return e >= 0 && (t = t.slice(0, e)), !t || t === "start";
  });
}
function lh(i, t, e) {
  var n, r, s = ah(t) ? kn : Lt;
  return function() {
    var o = s(this, i), a = o.on;
    a !== n && (r = (n = a).copy()).on(t, e), o.on = r;
  };
}
function ch(i, t) {
  var e = this._id;
  return arguments.length < 2 ? kt(this.node(), e).on.on(i) : this.each(lh(e, i, t));
}
function hh(i) {
  return function() {
    var t = this.parentNode;
    for (var e in this.__transition) if (+e !== i) return;
    t && t.removeChild(this);
  };
}
function dh() {
  return this.on("end.remove", hh(this._id));
}
function uh(i) {
  var t = this._name, e = this._id;
  typeof i != "function" && (i = Mn(i));
  for (var n = this._groups, r = n.length, s = new Array(r), o = 0; o < r; ++o)
    for (var a = n[o], c = a.length, l = s[o] = new Array(c), h, d, u = 0; u < c; ++u)
      (h = a[u]) && (d = i.call(h, h.__data__, u, a)) && ("__data__" in h && (d.__data__ = h.__data__), l[u] = d, bi(l[u], t, e, u, l, kt(h, e)));
  return new Ft(s, this._parents, t, e);
}
function ph(i) {
  var t = this._name, e = this._id;
  typeof i != "function" && (i = ns(i));
  for (var n = this._groups, r = n.length, s = [], o = [], a = 0; a < r; ++a)
    for (var c = n[a], l = c.length, h, d = 0; d < l; ++d)
      if (h = c[d]) {
        for (var u = i.call(h, h.__data__, d, c), p, g = kt(h, e), v = 0, y = u.length; v < y; ++v)
          (p = u[v]) && bi(p, t, e, v, u, g);
        s.push(u), o.push(h);
      }
  return new Ft(s, o, t, e);
}
var fh = ce.prototype.constructor;
function gh() {
  return new fh(this._groups, this._parents);
}
function mh(i, t) {
  var e, n, r;
  return function() {
    var s = oe(this, i), o = (this.style.removeProperty(i), oe(this, i));
    return s === o ? null : s === e && o === n ? r : r = t(e = s, n = o);
  };
}
function Es(i) {
  return function() {
    this.style.removeProperty(i);
  };
}
function vh(i, t, e) {
  var n, r = e + "", s;
  return function() {
    var o = oe(this, i);
    return o === r ? null : o === n ? s : s = t(n = o, e);
  };
}
function yh(i, t, e) {
  var n, r, s;
  return function() {
    var o = oe(this, i), a = e(this), c = a + "";
    return a == null && (c = a = (this.style.removeProperty(i), oe(this, i))), o === c ? null : o === n && c === r ? s : (r = c, s = t(n = o, a));
  };
}
function bh(i, t) {
  var e, n, r, s = "style." + t, o = "end." + s, a;
  return function() {
    var c = Lt(this, i), l = c.on, h = c.value[s] == null ? a || (a = Es(t)) : void 0;
    (l !== e || r !== h) && (n = (e = l).copy()).on(o, r = h), c.on = n;
  };
}
function wh(i, t, e) {
  var n = (i += "") == "transform" ? Nc : Ms;
  return t == null ? this.styleTween(i, mh(i, n)).on("end.style." + i, Es(i)) : typeof t == "function" ? this.styleTween(i, yh(i, n, An(this, "style." + i, t))).each(bh(this._id, i)) : this.styleTween(i, vh(i, n, t), e).on("end.style." + i, null);
}
function xh(i, t, e) {
  return function(n) {
    this.style.setProperty(i, t.call(this, n), e);
  };
}
function Ch(i, t, e) {
  var n, r;
  function s() {
    var o = t.apply(this, arguments);
    return o !== r && (n = (r = o) && xh(i, o, e)), n;
  }
  return s._value = t, s;
}
function Mh(i, t, e) {
  var n = "style." + (i += "");
  if (arguments.length < 2) return (n = this.tween(n)) && n._value;
  if (t == null) return this.tween(n, null);
  if (typeof t != "function") throw new Error();
  return this.tween(n, Ch(i, t, e ?? ""));
}
function Eh(i) {
  return function() {
    this.textContent = i;
  };
}
function Sh(i) {
  return function() {
    var t = i(this);
    this.textContent = t ?? "";
  };
}
function _h(i) {
  return this.tween("text", typeof i == "function" ? Sh(An(this, "text", i)) : Eh(i == null ? "" : i + ""));
}
function kh(i) {
  return function(t) {
    this.textContent = i.call(this, t);
  };
}
function Nh(i) {
  var t, e;
  function n() {
    var r = i.apply(this, arguments);
    return r !== e && (t = (e = r) && kh(r)), t;
  }
  return n._value = i, n;
}
function Ah(i) {
  var t = "text";
  if (arguments.length < 1) return (t = this.tween(t)) && t._value;
  if (i == null) return this.tween(t, null);
  if (typeof i != "function") throw new Error();
  return this.tween(t, Nh(i));
}
function Ih() {
  for (var i = this._name, t = this._id, e = Ss(), n = this._groups, r = n.length, s = 0; s < r; ++s)
    for (var o = n[s], a = o.length, c, l = 0; l < a; ++l)
      if (c = o[l]) {
        var h = kt(c, t);
        bi(c, i, e, l, o, {
          time: h.time + h.delay + h.duration,
          delay: 0,
          duration: h.duration,
          ease: h.ease
        });
      }
  return new Ft(n, this._parents, i, e);
}
function Lh() {
  var i, t, e = this, n = e._id, r = e.size();
  return new Promise(function(s, o) {
    var a = { value: o }, c = { value: function() {
      --r === 0 && s();
    } };
    e.each(function() {
      var l = Lt(this, n), h = l.on;
      h !== i && (t = (i = h).copy(), t._.cancel.push(a), t._.interrupt.push(a), t._.end.push(c)), l.on = t;
    }), r === 0 && s();
  });
}
var Oh = 0;
function Ft(i, t, e, n) {
  this._groups = i, this._parents = t, this._name = e, this._id = n;
}
function In(i) {
  return ce().transition(i);
}
function Ss() {
  return ++Oh;
}
var Tt = ce.prototype;
Ft.prototype = In.prototype = {
  constructor: Ft,
  select: uh,
  selectAll: ph,
  selectChild: Tt.selectChild,
  selectChildren: Tt.selectChildren,
  filter: sh,
  merge: oh,
  selection: gh,
  transition: Ih,
  call: Tt.call,
  nodes: Tt.nodes,
  node: Tt.node,
  size: Tt.size,
  empty: Tt.empty,
  each: Tt.each,
  on: ch,
  attr: qc,
  attrTween: Xc,
  style: wh,
  styleTween: Mh,
  text: _h,
  textTween: Ah,
  remove: dh,
  tween: Fc,
  delay: Zc,
  duration: th,
  ease: ih,
  easeVarying: rh,
  end: Lh,
  [Symbol.iterator]: Tt[Symbol.iterator]
};
function Th(i) {
  return ((i *= 2) <= 1 ? i * i * i : (i -= 2) * i * i + 2) / 2;
}
var Ph = {
  time: null,
  // Set on use.
  delay: 0,
  duration: 250,
  ease: Th
};
function Dh(i, t) {
  for (var e; !(e = i.__transition) || !(e = e[t]); )
    if (!(i = i.parentNode))
      throw new Error(`transition ${t} not found`);
  return e;
}
function Fh(i) {
  var t, e;
  i instanceof Ft ? (t = i._id, i = i._name) : (t = Ss(), (e = Ph).time = Sn(), i = i == null ? null : i + "");
  for (var n = this._groups, r = n.length, s = 0; s < r; ++s)
    for (var o = n[s], a = o.length, c, l = 0; l < a; ++l)
      (c = o[l]) && bi(c, i, t, l, o, e || Dh(c, t));
  return new Ft(n, this._parents, i, t);
}
ce.prototype.interrupt = ac;
ce.prototype.transition = Fh;
const zh = { passive: !1 }, Se = { capture: !0, passive: !1 };
function Bi(i) {
  i.stopImmediatePropagation();
}
function ne(i) {
  i.preventDefault(), i.stopImmediatePropagation();
}
function _s(i) {
  var t = i.document.documentElement, e = tt(i).on("dragstart.drag", ne, Se);
  "onselectstart" in t ? e.on("selectstart.drag", ne, Se) : (t.__noselect = t.style.MozUserSelect, t.style.MozUserSelect = "none");
}
function ks(i, t) {
  var e = i.document.documentElement, n = tt(i).on("dragstart.drag", null);
  t && (n.on("click.drag", ne, Se), setTimeout(function() {
    n.on("click.drag", null);
  }, 0)), "onselectstart" in e ? n.on("selectstart.drag", null) : (e.style.MozUserSelect = e.__noselect, delete e.__noselect);
}
const $e = (i) => () => i;
function pn(i, {
  sourceEvent: t,
  subject: e,
  target: n,
  identifier: r,
  active: s,
  x: o,
  y: a,
  dx: c,
  dy: l,
  dispatch: h
}) {
  Object.defineProperties(this, {
    type: { value: i, enumerable: !0, configurable: !0 },
    sourceEvent: { value: t, enumerable: !0, configurable: !0 },
    subject: { value: e, enumerable: !0, configurable: !0 },
    target: { value: n, enumerable: !0, configurable: !0 },
    identifier: { value: r, enumerable: !0, configurable: !0 },
    active: { value: s, enumerable: !0, configurable: !0 },
    x: { value: o, enumerable: !0, configurable: !0 },
    y: { value: a, enumerable: !0, configurable: !0 },
    dx: { value: c, enumerable: !0, configurable: !0 },
    dy: { value: l, enumerable: !0, configurable: !0 },
    _: { value: h }
  });
}
pn.prototype.on = function() {
  var i = this._.on.apply(this._, arguments);
  return i === this._ ? this : i;
};
function Bh(i) {
  return !i.ctrlKey && !i.button;
}
function Rh() {
  return this.parentNode;
}
function Hh(i, t) {
  return t ?? { x: i.x, y: i.y };
}
function $h() {
  return navigator.maxTouchPoints || "ontouchstart" in this;
}
function Gh() {
  var i = Bh, t = Rh, e = Hh, n = $h, r = {}, s = Ne("start", "drag", "end"), o = 0, a, c, l, h, d = 0;
  function u(C) {
    C.on("mousedown.drag", p).filter(n).on("touchstart.drag", y).on("touchmove.drag", b, zh).on("touchend.drag touchcancel.drag", x).style("touch-action", "none").style("-webkit-tap-highlight-color", "rgba(0,0,0,0)");
  }
  function p(C, N) {
    if (!(h || !i.call(this, C, N))) {
      var P = S(this, t.call(this, C, N), C, N, "mouse");
      P && (tt(C.view).on("mousemove.drag", g, Se).on("mouseup.drag", v, Se), _s(C.view), Bi(C), l = !1, a = C.clientX, c = C.clientY, P("start", C));
    }
  }
  function g(C) {
    if (ne(C), !l) {
      var N = C.clientX - a, P = C.clientY - c;
      l = N * N + P * P > d;
    }
    r.mouse("drag", C);
  }
  function v(C) {
    tt(C.view).on("mousemove.drag mouseup.drag", null), ks(C.view, l), ne(C), r.mouse("end", C);
  }
  function y(C, N) {
    if (i.call(this, C, N)) {
      var P = C.changedTouches, k = t.call(this, C, N), A = P.length, I, z;
      for (I = 0; I < A; ++I)
        (z = S(this, k, C, N, P[I].identifier, P[I])) && (Bi(C), z("start", C, P[I]));
    }
  }
  function b(C) {
    var N = C.changedTouches, P = N.length, k, A;
    for (k = 0; k < P; ++k)
      (A = r[N[k].identifier]) && (ne(C), A("drag", C, N[k]));
  }
  function x(C) {
    var N = C.changedTouches, P = N.length, k, A;
    for (h && clearTimeout(h), h = setTimeout(function() {
      h = null;
    }, 500), k = 0; k < P; ++k)
      (A = r[N[k].identifier]) && (Bi(C), A("end", C, N[k]));
  }
  function S(C, N, P, k, A, I) {
    var z = s.copy(), F = Pt(I || P, N), Z, Q, E;
    if ((E = e.call(C, new pn("beforestart", {
      sourceEvent: P,
      target: u,
      identifier: A,
      active: o,
      x: F[0],
      y: F[1],
      dx: 0,
      dy: 0,
      dispatch: z
    }), k)) != null)
      return Z = E.x - F[0] || 0, Q = E.y - F[1] || 0, function L(_, O, B) {
        var R = F, H;
        switch (_) {
          case "start":
            r[A] = L, H = o++;
            break;
          case "end":
            delete r[A], --o;
          // falls through
          case "drag":
            F = Pt(B || O, N), H = o;
            break;
        }
        z.call(
          _,
          C,
          new pn(_, {
            sourceEvent: O,
            subject: E,
            target: u,
            identifier: A,
            active: H,
            x: F[0] + Z,
            y: F[1] + Q,
            dx: F[0] - R[0],
            dy: F[1] - R[1],
            dispatch: z
          }),
          k
        );
      };
  }
  return u.filter = function(C) {
    return arguments.length ? (i = typeof C == "function" ? C : $e(!!C), u) : i;
  }, u.container = function(C) {
    return arguments.length ? (t = typeof C == "function" ? C : $e(C), u) : t;
  }, u.subject = function(C) {
    return arguments.length ? (e = typeof C == "function" ? C : $e(C), u) : e;
  }, u.touchable = function(C) {
    return arguments.length ? (n = typeof C == "function" ? C : $e(!!C), u) : n;
  }, u.on = function() {
    var C = s.on.apply(s, arguments);
    return C === s ? u : C;
  }, u.clickDistance = function(C) {
    return arguments.length ? (d = (C = +C) * C, u) : Math.sqrt(d);
  }, u;
}
const Ge = (i) => () => i;
function qh(i, {
  sourceEvent: t,
  target: e,
  transform: n,
  dispatch: r
}) {
  Object.defineProperties(this, {
    type: { value: i, enumerable: !0, configurable: !0 },
    sourceEvent: { value: t, enumerable: !0, configurable: !0 },
    target: { value: e, enumerable: !0, configurable: !0 },
    transform: { value: n, enumerable: !0, configurable: !0 },
    _: { value: r }
  });
}
function Dt(i, t, e) {
  this.k = i, this.x = t, this.y = e;
}
Dt.prototype = {
  constructor: Dt,
  scale: function(i) {
    return i === 1 ? this : new Dt(this.k * i, this.x, this.y);
  },
  translate: function(i, t) {
    return i === 0 & t === 0 ? this : new Dt(this.k, this.x + this.k * i, this.y + this.k * t);
  },
  apply: function(i) {
    return [i[0] * this.k + this.x, i[1] * this.k + this.y];
  },
  applyX: function(i) {
    return i * this.k + this.x;
  },
  applyY: function(i) {
    return i * this.k + this.y;
  },
  invert: function(i) {
    return [(i[0] - this.x) / this.k, (i[1] - this.y) / this.k];
  },
  invertX: function(i) {
    return (i - this.x) / this.k;
  },
  invertY: function(i) {
    return (i - this.y) / this.k;
  },
  rescaleX: function(i) {
    return i.copy().domain(i.range().map(this.invertX, this).map(i.invert, i));
  },
  rescaleY: function(i) {
    return i.copy().domain(i.range().map(this.invertY, this).map(i.invert, i));
  },
  toString: function() {
    return "translate(" + this.x + "," + this.y + ") scale(" + this.k + ")";
  }
};
var ui = new Dt(1, 0, 0);
Dt.prototype;
function Ri(i) {
  i.stopImmediatePropagation();
}
function fe(i) {
  i.preventDefault(), i.stopImmediatePropagation();
}
function Vh(i) {
  return (!i.ctrlKey || i.type === "wheel") && !i.button;
}
function Uh() {
  var i = this;
  return i instanceof SVGElement ? (i = i.ownerSVGElement || i, i.hasAttribute("viewBox") ? (i = i.viewBox.baseVal, [[i.x, i.y], [i.x + i.width, i.y + i.height]]) : [[0, 0], [i.width.baseVal.value, i.height.baseVal.value]]) : [[0, 0], [i.clientWidth, i.clientHeight]];
}
function br() {
  return this.__zoom || ui;
}
function jh(i) {
  return -i.deltaY * (i.deltaMode === 1 ? 0.05 : i.deltaMode ? 1 : 2e-3) * (i.ctrlKey ? 10 : 1);
}
function Yh() {
  return navigator.maxTouchPoints || "ontouchstart" in this;
}
function Xh(i, t, e) {
  var n = i.invertX(t[0][0]) - e[0][0], r = i.invertX(t[1][0]) - e[1][0], s = i.invertY(t[0][1]) - e[0][1], o = i.invertY(t[1][1]) - e[1][1];
  return i.translate(
    r > n ? (n + r) / 2 : Math.min(0, n) || Math.max(0, r),
    o > s ? (s + o) / 2 : Math.min(0, s) || Math.max(0, o)
  );
}
function Wh() {
  var i = Vh, t = Uh, e = Xh, n = jh, r = Yh, s = [0, 1 / 0], o = [[-1 / 0, -1 / 0], [1 / 0, 1 / 0]], a = 250, c = Tc, l = Ne("start", "zoom", "end"), h, d, u, p = 500, g = 150, v = 0, y = 10;
  function b(E) {
    E.property("__zoom", br).on("wheel.zoom", A, { passive: !1 }).on("mousedown.zoom", I).on("dblclick.zoom", z).filter(r).on("touchstart.zoom", F).on("touchmove.zoom", Z).on("touchend.zoom touchcancel.zoom", Q).style("-webkit-tap-highlight-color", "rgba(0,0,0,0)");
  }
  b.transform = function(E, L, _, O) {
    var B = E.selection ? E.selection() : E;
    B.property("__zoom", br), E !== B ? N(E, L, _, O) : B.interrupt().each(function() {
      P(this, arguments).event(O).start().zoom(null, typeof L == "function" ? L.apply(this, arguments) : L).end();
    });
  }, b.scaleBy = function(E, L, _, O) {
    b.scaleTo(E, function() {
      var B = this.__zoom.k, R = typeof L == "function" ? L.apply(this, arguments) : L;
      return B * R;
    }, _, O);
  }, b.scaleTo = function(E, L, _, O) {
    b.transform(E, function() {
      var B = t.apply(this, arguments), R = this.__zoom, H = _ == null ? C(B) : typeof _ == "function" ? _.apply(this, arguments) : _, V = R.invert(H), j = typeof L == "function" ? L.apply(this, arguments) : L;
      return e(S(x(R, j), H, V), B, o);
    }, _, O);
  }, b.translateBy = function(E, L, _, O) {
    b.transform(E, function() {
      return e(this.__zoom.translate(
        typeof L == "function" ? L.apply(this, arguments) : L,
        typeof _ == "function" ? _.apply(this, arguments) : _
      ), t.apply(this, arguments), o);
    }, null, O);
  }, b.translateTo = function(E, L, _, O, B) {
    b.transform(E, function() {
      var R = t.apply(this, arguments), H = this.__zoom, V = O == null ? C(R) : typeof O == "function" ? O.apply(this, arguments) : O;
      return e(ui.translate(V[0], V[1]).scale(H.k).translate(
        typeof L == "function" ? -L.apply(this, arguments) : -L,
        typeof _ == "function" ? -_.apply(this, arguments) : -_
      ), R, o);
    }, O, B);
  };
  function x(E, L) {
    return L = Math.max(s[0], Math.min(s[1], L)), L === E.k ? E : new Dt(L, E.x, E.y);
  }
  function S(E, L, _) {
    var O = L[0] - _[0] * E.k, B = L[1] - _[1] * E.k;
    return O === E.x && B === E.y ? E : new Dt(E.k, O, B);
  }
  function C(E) {
    return [(+E[0][0] + +E[1][0]) / 2, (+E[0][1] + +E[1][1]) / 2];
  }
  function N(E, L, _, O) {
    E.on("start.zoom", function() {
      P(this, arguments).event(O).start();
    }).on("interrupt.zoom end.zoom", function() {
      P(this, arguments).event(O).end();
    }).tween("zoom", function() {
      var B = this, R = arguments, H = P(B, R).event(O), V = t.apply(B, R), j = _ == null ? C(V) : typeof _ == "function" ? _.apply(B, R) : _, $ = Math.max(V[1][0] - V[0][0], V[1][1] - V[0][1]), et = B.__zoom, mt = typeof L == "function" ? L.apply(B, R) : L, lt = c(et.invert(j).concat($ / et.k), mt.invert(j).concat($ / mt.k));
      return function(pt) {
        if (pt === 1) pt = mt;
        else {
          var ct = lt(pt), Zt = $ / ct[2];
          pt = new Dt(Zt, j[0] - ct[0] * Zt, j[1] - ct[1] * Zt);
        }
        H.zoom(null, pt);
      };
    });
  }
  function P(E, L, _) {
    return !_ && E.__zooming || new k(E, L);
  }
  function k(E, L) {
    this.that = E, this.args = L, this.active = 0, this.sourceEvent = null, this.extent = t.apply(E, L), this.taps = 0;
  }
  k.prototype = {
    event: function(E) {
      return E && (this.sourceEvent = E), this;
    },
    start: function() {
      return ++this.active === 1 && (this.that.__zooming = this, this.emit("start")), this;
    },
    zoom: function(E, L) {
      return this.mouse && E !== "mouse" && (this.mouse[1] = L.invert(this.mouse[0])), this.touch0 && E !== "touch" && (this.touch0[1] = L.invert(this.touch0[0])), this.touch1 && E !== "touch" && (this.touch1[1] = L.invert(this.touch1[0])), this.that.__zoom = L, this.emit("zoom"), this;
    },
    end: function() {
      return --this.active === 0 && (delete this.that.__zooming, this.emit("end")), this;
    },
    emit: function(E) {
      var L = tt(this.that).datum();
      l.call(
        E,
        this.that,
        new qh(E, {
          sourceEvent: this.sourceEvent,
          target: b,
          transform: this.that.__zoom,
          dispatch: l
        }),
        L
      );
    }
  };
  function A(E, ...L) {
    if (!i.apply(this, arguments)) return;
    var _ = P(this, L).event(E), O = this.__zoom, B = Math.max(s[0], Math.min(s[1], O.k * Math.pow(2, n.apply(this, arguments)))), R = Pt(E);
    if (_.wheel)
      (_.mouse[0][0] !== R[0] || _.mouse[0][1] !== R[1]) && (_.mouse[1] = O.invert(_.mouse[0] = R)), clearTimeout(_.wheel);
    else {
      if (O.k === B) return;
      _.mouse = [R, O.invert(R)], ti(this), _.start();
    }
    fe(E), _.wheel = setTimeout(H, g), _.zoom("mouse", e(S(x(O, B), _.mouse[0], _.mouse[1]), _.extent, o));
    function H() {
      _.wheel = null, _.end();
    }
  }
  function I(E, ...L) {
    if (u || !i.apply(this, arguments)) return;
    var _ = E.currentTarget, O = P(this, L, !0).event(E), B = tt(E.view).on("mousemove.zoom", j, !0).on("mouseup.zoom", $, !0), R = Pt(E, _), H = E.clientX, V = E.clientY;
    _s(E.view), Ri(E), O.mouse = [R, this.__zoom.invert(R)], ti(this), O.start();
    function j(et) {
      if (fe(et), !O.moved) {
        var mt = et.clientX - H, lt = et.clientY - V;
        O.moved = mt * mt + lt * lt > v;
      }
      O.event(et).zoom("mouse", e(S(O.that.__zoom, O.mouse[0] = Pt(et, _), O.mouse[1]), O.extent, o));
    }
    function $(et) {
      B.on("mousemove.zoom mouseup.zoom", null), ks(et.view, O.moved), fe(et), O.event(et).end();
    }
  }
  function z(E, ...L) {
    if (i.apply(this, arguments)) {
      var _ = this.__zoom, O = Pt(E.changedTouches ? E.changedTouches[0] : E, this), B = _.invert(O), R = _.k * (E.shiftKey ? 0.5 : 2), H = e(S(x(_, R), O, B), t.apply(this, L), o);
      fe(E), a > 0 ? tt(this).transition().duration(a).call(N, H, O, E) : tt(this).call(b.transform, H, O, E);
    }
  }
  function F(E, ...L) {
    if (i.apply(this, arguments)) {
      var _ = E.touches, O = _.length, B = P(this, L, E.changedTouches.length === O).event(E), R, H, V, j;
      for (Ri(E), H = 0; H < O; ++H)
        V = _[H], j = Pt(V, this), j = [j, this.__zoom.invert(j), V.identifier], B.touch0 ? !B.touch1 && B.touch0[2] !== j[2] && (B.touch1 = j, B.taps = 0) : (B.touch0 = j, R = !0, B.taps = 1 + !!h);
      h && (h = clearTimeout(h)), R && (B.taps < 2 && (d = j[0], h = setTimeout(function() {
        h = null;
      }, p)), ti(this), B.start());
    }
  }
  function Z(E, ...L) {
    if (this.__zooming) {
      var _ = P(this, L).event(E), O = E.changedTouches, B = O.length, R, H, V, j;
      for (fe(E), R = 0; R < B; ++R)
        H = O[R], V = Pt(H, this), _.touch0 && _.touch0[2] === H.identifier ? _.touch0[0] = V : _.touch1 && _.touch1[2] === H.identifier && (_.touch1[0] = V);
      if (H = _.that.__zoom, _.touch1) {
        var $ = _.touch0[0], et = _.touch0[1], mt = _.touch1[0], lt = _.touch1[1], pt = (pt = mt[0] - $[0]) * pt + (pt = mt[1] - $[1]) * pt, ct = (ct = lt[0] - et[0]) * ct + (ct = lt[1] - et[1]) * ct;
        H = x(H, Math.sqrt(pt / ct)), V = [($[0] + mt[0]) / 2, ($[1] + mt[1]) / 2], j = [(et[0] + lt[0]) / 2, (et[1] + lt[1]) / 2];
      } else if (_.touch0) V = _.touch0[0], j = _.touch0[1];
      else return;
      _.zoom("touch", e(S(H, V, j), _.extent, o));
    }
  }
  function Q(E, ...L) {
    if (this.__zooming) {
      var _ = P(this, L).event(E), O = E.changedTouches, B = O.length, R, H;
      for (Ri(E), u && clearTimeout(u), u = setTimeout(function() {
        u = null;
      }, p), R = 0; R < B; ++R)
        H = O[R], _.touch0 && _.touch0[2] === H.identifier ? delete _.touch0 : _.touch1 && _.touch1[2] === H.identifier && delete _.touch1;
      if (_.touch1 && !_.touch0 && (_.touch0 = _.touch1, delete _.touch1), _.touch0) _.touch0[1] = this.__zoom.invert(_.touch0[0]);
      else if (_.end(), _.taps === 2 && (H = Pt(H, this), Math.hypot(d[0] - H[0], d[1] - H[1]) < y)) {
        var V = tt(this).on("dblclick.zoom");
        V && V.apply(this, arguments);
      }
    }
  }
  return b.wheelDelta = function(E) {
    return arguments.length ? (n = typeof E == "function" ? E : Ge(+E), b) : n;
  }, b.filter = function(E) {
    return arguments.length ? (i = typeof E == "function" ? E : Ge(!!E), b) : i;
  }, b.touchable = function(E) {
    return arguments.length ? (r = typeof E == "function" ? E : Ge(!!E), b) : r;
  }, b.extent = function(E) {
    return arguments.length ? (t = typeof E == "function" ? E : Ge([[+E[0][0], +E[0][1]], [+E[1][0], +E[1][1]]]), b) : t;
  }, b.scaleExtent = function(E) {
    return arguments.length ? (s[0] = +E[0], s[1] = +E[1], b) : [s[0], s[1]];
  }, b.translateExtent = function(E) {
    return arguments.length ? (o[0][0] = +E[0][0], o[1][0] = +E[1][0], o[0][1] = +E[0][1], o[1][1] = +E[1][1], b) : [[o[0][0], o[0][1]], [o[1][0], o[1][1]]];
  }, b.constrain = function(E) {
    return arguments.length ? (e = E, b) : e;
  }, b.duration = function(E) {
    return arguments.length ? (a = +E, b) : a;
  }, b.interpolate = function(E) {
    return arguments.length ? (c = E, b) : c;
  }, b.on = function() {
    var E = l.on.apply(l, arguments);
    return E === l ? b : E;
  }, b.clickDistance = function(E) {
    return arguments.length ? (v = (E = +E) * E, b) : Math.sqrt(v);
  }, b.tapDistance = function(E) {
    return arguments.length ? (y = +E, b) : y;
  }, b;
}
function Kh(i, t) {
  var e, n = 1;
  i == null && (i = 0), t == null && (t = 0);
  function r() {
    var s, o = e.length, a, c = 0, l = 0;
    for (s = 0; s < o; ++s)
      a = e[s], c += a.x, l += a.y;
    for (c = (c / o - i) * n, l = (l / o - t) * n, s = 0; s < o; ++s)
      a = e[s], a.x -= c, a.y -= l;
  }
  return r.initialize = function(s) {
    e = s;
  }, r.x = function(s) {
    return arguments.length ? (i = +s, r) : i;
  }, r.y = function(s) {
    return arguments.length ? (t = +s, r) : t;
  }, r.strength = function(s) {
    return arguments.length ? (n = +s, r) : n;
  }, r;
}
function Zh(i) {
  const t = +this._x.call(null, i), e = +this._y.call(null, i);
  return Ns(this.cover(t, e), t, e, i);
}
function Ns(i, t, e, n) {
  if (isNaN(t) || isNaN(e)) return i;
  var r, s = i._root, o = { data: n }, a = i._x0, c = i._y0, l = i._x1, h = i._y1, d, u, p, g, v, y, b, x;
  if (!s) return i._root = o, i;
  for (; s.length; )
    if ((v = t >= (d = (a + l) / 2)) ? a = d : l = d, (y = e >= (u = (c + h) / 2)) ? c = u : h = u, r = s, !(s = s[b = y << 1 | v])) return r[b] = o, i;
  if (p = +i._x.call(null, s.data), g = +i._y.call(null, s.data), t === p && e === g) return o.next = s, r ? r[b] = o : i._root = o, i;
  do
    r = r ? r[b] = new Array(4) : i._root = new Array(4), (v = t >= (d = (a + l) / 2)) ? a = d : l = d, (y = e >= (u = (c + h) / 2)) ? c = u : h = u;
  while ((b = y << 1 | v) === (x = (g >= u) << 1 | p >= d));
  return r[x] = s, r[b] = o, i;
}
function Qh(i) {
  var t, e, n = i.length, r, s, o = new Array(n), a = new Array(n), c = 1 / 0, l = 1 / 0, h = -1 / 0, d = -1 / 0;
  for (e = 0; e < n; ++e)
    isNaN(r = +this._x.call(null, t = i[e])) || isNaN(s = +this._y.call(null, t)) || (o[e] = r, a[e] = s, r < c && (c = r), r > h && (h = r), s < l && (l = s), s > d && (d = s));
  if (c > h || l > d) return this;
  for (this.cover(c, l).cover(h, d), e = 0; e < n; ++e)
    Ns(this, o[e], a[e], i[e]);
  return this;
}
function Jh(i, t) {
  if (isNaN(i = +i) || isNaN(t = +t)) return this;
  var e = this._x0, n = this._y0, r = this._x1, s = this._y1;
  if (isNaN(e))
    r = (e = Math.floor(i)) + 1, s = (n = Math.floor(t)) + 1;
  else {
    for (var o = r - e || 1, a = this._root, c, l; e > i || i >= r || n > t || t >= s; )
      switch (l = (t < n) << 1 | i < e, c = new Array(4), c[l] = a, a = c, o *= 2, l) {
        case 0:
          r = e + o, s = n + o;
          break;
        case 1:
          e = r - o, s = n + o;
          break;
        case 2:
          r = e + o, n = s - o;
          break;
        case 3:
          e = r - o, n = s - o;
          break;
      }
    this._root && this._root.length && (this._root = a);
  }
  return this._x0 = e, this._y0 = n, this._x1 = r, this._y1 = s, this;
}
function td() {
  var i = [];
  return this.visit(function(t) {
    if (!t.length) do
      i.push(t.data);
    while (t = t.next);
  }), i;
}
function ed(i) {
  return arguments.length ? this.cover(+i[0][0], +i[0][1]).cover(+i[1][0], +i[1][1]) : isNaN(this._x0) ? void 0 : [[this._x0, this._y0], [this._x1, this._y1]];
}
function dt(i, t, e, n, r) {
  this.node = i, this.x0 = t, this.y0 = e, this.x1 = n, this.y1 = r;
}
function id(i, t, e) {
  var n, r = this._x0, s = this._y0, o, a, c, l, h = this._x1, d = this._y1, u = [], p = this._root, g, v;
  for (p && u.push(new dt(p, r, s, h, d)), e == null ? e = 1 / 0 : (r = i - e, s = t - e, h = i + e, d = t + e, e *= e); g = u.pop(); )
    if (!(!(p = g.node) || (o = g.x0) > h || (a = g.y0) > d || (c = g.x1) < r || (l = g.y1) < s))
      if (p.length) {
        var y = (o + c) / 2, b = (a + l) / 2;
        u.push(
          new dt(p[3], y, b, c, l),
          new dt(p[2], o, b, y, l),
          new dt(p[1], y, a, c, b),
          new dt(p[0], o, a, y, b)
        ), (v = (t >= b) << 1 | i >= y) && (g = u[u.length - 1], u[u.length - 1] = u[u.length - 1 - v], u[u.length - 1 - v] = g);
      } else {
        var x = i - +this._x.call(null, p.data), S = t - +this._y.call(null, p.data), C = x * x + S * S;
        if (C < e) {
          var N = Math.sqrt(e = C);
          r = i - N, s = t - N, h = i + N, d = t + N, n = p.data;
        }
      }
  return n;
}
function nd(i) {
  if (isNaN(h = +this._x.call(null, i)) || isNaN(d = +this._y.call(null, i))) return this;
  var t, e = this._root, n, r, s, o = this._x0, a = this._y0, c = this._x1, l = this._y1, h, d, u, p, g, v, y, b;
  if (!e) return this;
  if (e.length) for (; ; ) {
    if ((g = h >= (u = (o + c) / 2)) ? o = u : c = u, (v = d >= (p = (a + l) / 2)) ? a = p : l = p, t = e, !(e = e[y = v << 1 | g])) return this;
    if (!e.length) break;
    (t[y + 1 & 3] || t[y + 2 & 3] || t[y + 3 & 3]) && (n = t, b = y);
  }
  for (; e.data !== i; ) if (r = e, !(e = e.next)) return this;
  return (s = e.next) && delete e.next, r ? (s ? r.next = s : delete r.next, this) : t ? (s ? t[y] = s : delete t[y], (e = t[0] || t[1] || t[2] || t[3]) && e === (t[3] || t[2] || t[1] || t[0]) && !e.length && (n ? n[b] = e : this._root = e), this) : (this._root = s, this);
}
function rd(i) {
  for (var t = 0, e = i.length; t < e; ++t) this.remove(i[t]);
  return this;
}
function sd() {
  return this._root;
}
function od() {
  var i = 0;
  return this.visit(function(t) {
    if (!t.length) do
      ++i;
    while (t = t.next);
  }), i;
}
function ad(i) {
  var t = [], e, n = this._root, r, s, o, a, c;
  for (n && t.push(new dt(n, this._x0, this._y0, this._x1, this._y1)); e = t.pop(); )
    if (!i(n = e.node, s = e.x0, o = e.y0, a = e.x1, c = e.y1) && n.length) {
      var l = (s + a) / 2, h = (o + c) / 2;
      (r = n[3]) && t.push(new dt(r, l, h, a, c)), (r = n[2]) && t.push(new dt(r, s, h, l, c)), (r = n[1]) && t.push(new dt(r, l, o, a, h)), (r = n[0]) && t.push(new dt(r, s, o, l, h));
    }
  return this;
}
function ld(i) {
  var t = [], e = [], n;
  for (this._root && t.push(new dt(this._root, this._x0, this._y0, this._x1, this._y1)); n = t.pop(); ) {
    var r = n.node;
    if (r.length) {
      var s, o = n.x0, a = n.y0, c = n.x1, l = n.y1, h = (o + c) / 2, d = (a + l) / 2;
      (s = r[0]) && t.push(new dt(s, o, a, h, d)), (s = r[1]) && t.push(new dt(s, h, a, c, d)), (s = r[2]) && t.push(new dt(s, o, d, h, l)), (s = r[3]) && t.push(new dt(s, h, d, c, l));
    }
    e.push(n);
  }
  for (; n = e.pop(); )
    i(n.node, n.x0, n.y0, n.x1, n.y1);
  return this;
}
function cd(i) {
  return i[0];
}
function hd(i) {
  return arguments.length ? (this._x = i, this) : this._x;
}
function dd(i) {
  return i[1];
}
function ud(i) {
  return arguments.length ? (this._y = i, this) : this._y;
}
function Ln(i, t, e) {
  var n = new On(t ?? cd, e ?? dd, NaN, NaN, NaN, NaN);
  return i == null ? n : n.addAll(i);
}
function On(i, t, e, n, r, s) {
  this._x = i, this._y = t, this._x0 = e, this._y0 = n, this._x1 = r, this._y1 = s, this._root = void 0;
}
function wr(i) {
  for (var t = { data: i.data }, e = t; i = i.next; ) e = e.next = { data: i.data };
  return t;
}
var ut = Ln.prototype = On.prototype;
ut.copy = function() {
  var i = new On(this._x, this._y, this._x0, this._y0, this._x1, this._y1), t = this._root, e, n;
  if (!t) return i;
  if (!t.length) return i._root = wr(t), i;
  for (e = [{ source: t, target: i._root = new Array(4) }]; t = e.pop(); )
    for (var r = 0; r < 4; ++r)
      (n = t.source[r]) && (n.length ? e.push({ source: n, target: t.target[r] = new Array(4) }) : t.target[r] = wr(n));
  return i;
};
ut.add = Zh;
ut.addAll = Qh;
ut.cover = Jh;
ut.data = td;
ut.extent = ed;
ut.find = id;
ut.remove = nd;
ut.removeAll = rd;
ut.root = sd;
ut.size = od;
ut.visit = ad;
ut.visitAfter = ld;
ut.x = hd;
ut.y = ud;
function nt(i) {
  return function() {
    return i;
  };
}
function Ht(i) {
  return (i() - 0.5) * 1e-6;
}
function pd(i) {
  return i.x + i.vx;
}
function fd(i) {
  return i.y + i.vy;
}
function gd(i) {
  var t, e, n, r = 1, s = 1;
  typeof i != "function" && (i = nt(i == null ? 1 : +i));
  function o() {
    for (var l, h = t.length, d, u, p, g, v, y, b = 0; b < s; ++b)
      for (d = Ln(t, pd, fd).visitAfter(a), l = 0; l < h; ++l)
        u = t[l], v = e[u.index], y = v * v, p = u.x + u.vx, g = u.y + u.vy, d.visit(x);
    function x(S, C, N, P, k) {
      var A = S.data, I = S.r, z = v + I;
      if (A) {
        if (A.index > u.index) {
          var F = p - A.x - A.vx, Z = g - A.y - A.vy, Q = F * F + Z * Z;
          Q < z * z && (F === 0 && (F = Ht(n), Q += F * F), Z === 0 && (Z = Ht(n), Q += Z * Z), Q = (z - (Q = Math.sqrt(Q))) / Q * r, u.vx += (F *= Q) * (z = (I *= I) / (y + I)), u.vy += (Z *= Q) * z, A.vx -= F * (z = 1 - z), A.vy -= Z * z);
        }
        return;
      }
      return C > p + z || P < p - z || N > g + z || k < g - z;
    }
  }
  function a(l) {
    if (l.data) return l.r = e[l.data.index];
    for (var h = l.r = 0; h < 4; ++h)
      l[h] && l[h].r > l.r && (l.r = l[h].r);
  }
  function c() {
    if (t) {
      var l, h = t.length, d;
      for (e = new Array(h), l = 0; l < h; ++l) d = t[l], e[d.index] = +i(d, l, t);
    }
  }
  return o.initialize = function(l, h) {
    t = l, n = h, c();
  }, o.iterations = function(l) {
    return arguments.length ? (s = +l, o) : s;
  }, o.strength = function(l) {
    return arguments.length ? (r = +l, o) : r;
  }, o.radius = function(l) {
    return arguments.length ? (i = typeof l == "function" ? l : nt(+l), c(), o) : i;
  }, o;
}
function md(i) {
  return i.index;
}
function xr(i, t) {
  var e = i.get(t);
  if (!e) throw new Error("node not found: " + t);
  return e;
}
function vd(i) {
  var t = md, e = d, n, r = nt(30), s, o, a, c, l, h = 1;
  i == null && (i = []);
  function d(y) {
    return 1 / Math.min(a[y.source.index], a[y.target.index]);
  }
  function u(y) {
    for (var b = 0, x = i.length; b < h; ++b)
      for (var S = 0, C, N, P, k, A, I, z; S < x; ++S)
        C = i[S], N = C.source, P = C.target, k = P.x + P.vx - N.x - N.vx || Ht(l), A = P.y + P.vy - N.y - N.vy || Ht(l), I = Math.sqrt(k * k + A * A), I = (I - s[S]) / I * y * n[S], k *= I, A *= I, P.vx -= k * (z = c[S]), P.vy -= A * z, N.vx += k * (z = 1 - z), N.vy += A * z;
  }
  function p() {
    if (o) {
      var y, b = o.length, x = i.length, S = new Map(o.map((N, P) => [t(N, P, o), N])), C;
      for (y = 0, a = new Array(b); y < x; ++y)
        C = i[y], C.index = y, typeof C.source != "object" && (C.source = xr(S, C.source)), typeof C.target != "object" && (C.target = xr(S, C.target)), a[C.source.index] = (a[C.source.index] || 0) + 1, a[C.target.index] = (a[C.target.index] || 0) + 1;
      for (y = 0, c = new Array(x); y < x; ++y)
        C = i[y], c[y] = a[C.source.index] / (a[C.source.index] + a[C.target.index]);
      n = new Array(x), g(), s = new Array(x), v();
    }
  }
  function g() {
    if (o)
      for (var y = 0, b = i.length; y < b; ++y)
        n[y] = +e(i[y], y, i);
  }
  function v() {
    if (o)
      for (var y = 0, b = i.length; y < b; ++y)
        s[y] = +r(i[y], y, i);
  }
  return u.initialize = function(y, b) {
    o = y, l = b, p();
  }, u.links = function(y) {
    return arguments.length ? (i = y, p(), u) : i;
  }, u.id = function(y) {
    return arguments.length ? (t = y, u) : t;
  }, u.iterations = function(y) {
    return arguments.length ? (h = +y, u) : h;
  }, u.strength = function(y) {
    return arguments.length ? (e = typeof y == "function" ? y : nt(+y), g(), u) : e;
  }, u.distance = function(y) {
    return arguments.length ? (r = typeof y == "function" ? y : nt(+y), v(), u) : r;
  }, u;
}
const yd = 1664525, bd = 1013904223, Cr = 4294967296;
function wd() {
  let i = 1;
  return () => (i = (yd * i + bd) % Cr) / Cr;
}
function xd(i) {
  return i.x;
}
function Cd(i) {
  return i.y;
}
var Md = 10, Ed = Math.PI * (3 - Math.sqrt(5));
function Sd(i) {
  var t, e = 1, n = 1e-3, r = 1 - Math.pow(n, 1 / 300), s = 0, o = 0.6, a = /* @__PURE__ */ new Map(), c = _n(d), l = Ne("tick", "end"), h = wd();
  i == null && (i = []);
  function d() {
    u(), l.call("tick", t), e < n && (c.stop(), l.call("end", t));
  }
  function u(v) {
    var y, b = i.length, x;
    v === void 0 && (v = 1);
    for (var S = 0; S < v; ++S)
      for (e += (s - e) * r, a.forEach(function(C) {
        C(e);
      }), y = 0; y < b; ++y)
        x = i[y], x.fx == null ? x.x += x.vx *= o : (x.x = x.fx, x.vx = 0), x.fy == null ? x.y += x.vy *= o : (x.y = x.fy, x.vy = 0);
    return t;
  }
  function p() {
    for (var v = 0, y = i.length, b; v < y; ++v) {
      if (b = i[v], b.index = v, b.fx != null && (b.x = b.fx), b.fy != null && (b.y = b.fy), isNaN(b.x) || isNaN(b.y)) {
        var x = Md * Math.sqrt(0.5 + v), S = v * Ed;
        b.x = x * Math.cos(S), b.y = x * Math.sin(S);
      }
      (isNaN(b.vx) || isNaN(b.vy)) && (b.vx = b.vy = 0);
    }
  }
  function g(v) {
    return v.initialize && v.initialize(i, h), v;
  }
  return p(), t = {
    tick: u,
    restart: function() {
      return c.restart(d), t;
    },
    stop: function() {
      return c.stop(), t;
    },
    nodes: function(v) {
      return arguments.length ? (i = v, p(), a.forEach(g), t) : i;
    },
    alpha: function(v) {
      return arguments.length ? (e = +v, t) : e;
    },
    alphaMin: function(v) {
      return arguments.length ? (n = +v, t) : n;
    },
    alphaDecay: function(v) {
      return arguments.length ? (r = +v, t) : +r;
    },
    alphaTarget: function(v) {
      return arguments.length ? (s = +v, t) : s;
    },
    velocityDecay: function(v) {
      return arguments.length ? (o = 1 - v, t) : 1 - o;
    },
    randomSource: function(v) {
      return arguments.length ? (h = v, a.forEach(g), t) : h;
    },
    force: function(v, y) {
      return arguments.length > 1 ? (y == null ? a.delete(v) : a.set(v, g(y)), t) : a.get(v);
    },
    find: function(v, y, b) {
      var x = 0, S = i.length, C, N, P, k, A;
      for (b == null ? b = 1 / 0 : b *= b, x = 0; x < S; ++x)
        k = i[x], C = v - k.x, N = y - k.y, P = C * C + N * N, P < b && (A = k, b = P);
      return A;
    },
    on: function(v, y) {
      return arguments.length > 1 ? (l.on(v, y), t) : l.on(v);
    }
  };
}
function _d() {
  var i, t, e, n, r = nt(-30), s, o = 1, a = 1 / 0, c = 0.81;
  function l(p) {
    var g, v = i.length, y = Ln(i, xd, Cd).visitAfter(d);
    for (n = p, g = 0; g < v; ++g) t = i[g], y.visit(u);
  }
  function h() {
    if (i) {
      var p, g = i.length, v;
      for (s = new Array(g), p = 0; p < g; ++p) v = i[p], s[v.index] = +r(v, p, i);
    }
  }
  function d(p) {
    var g = 0, v, y, b = 0, x, S, C;
    if (p.length) {
      for (x = S = C = 0; C < 4; ++C)
        (v = p[C]) && (y = Math.abs(v.value)) && (g += v.value, b += y, x += y * v.x, S += y * v.y);
      p.x = x / b, p.y = S / b;
    } else {
      v = p, v.x = v.data.x, v.y = v.data.y;
      do
        g += s[v.data.index];
      while (v = v.next);
    }
    p.value = g;
  }
  function u(p, g, v, y) {
    if (!p.value) return !0;
    var b = p.x - t.x, x = p.y - t.y, S = y - g, C = b * b + x * x;
    if (S * S / c < C)
      return C < a && (b === 0 && (b = Ht(e), C += b * b), x === 0 && (x = Ht(e), C += x * x), C < o && (C = Math.sqrt(o * C)), t.vx += b * p.value * n / C, t.vy += x * p.value * n / C), !0;
    if (p.length || C >= a) return;
    (p.data !== t || p.next) && (b === 0 && (b = Ht(e), C += b * b), x === 0 && (x = Ht(e), C += x * x), C < o && (C = Math.sqrt(o * C)));
    do
      p.data !== t && (S = s[p.data.index] * n / C, t.vx += b * S, t.vy += x * S);
    while (p = p.next);
  }
  return l.initialize = function(p, g) {
    i = p, e = g, h();
  }, l.strength = function(p) {
    return arguments.length ? (r = typeof p == "function" ? p : nt(+p), h(), l) : r;
  }, l.distanceMin = function(p) {
    return arguments.length ? (o = p * p, l) : Math.sqrt(o);
  }, l.distanceMax = function(p) {
    return arguments.length ? (a = p * p, l) : Math.sqrt(a);
  }, l.theta = function(p) {
    return arguments.length ? (c = p * p, l) : Math.sqrt(c);
  }, l;
}
function Mr(i, t, e) {
  var n, r = nt(0.1), s, o;
  typeof i != "function" && (i = nt(+i)), t == null && (t = 0), e == null && (e = 0);
  function a(l) {
    for (var h = 0, d = n.length; h < d; ++h) {
      var u = n[h], p = u.x - t || 1e-6, g = u.y - e || 1e-6, v = Math.sqrt(p * p + g * g), y = (o[h] - v) * s[h] * l / v;
      u.vx += p * y, u.vy += g * y;
    }
  }
  function c() {
    if (n) {
      var l, h = n.length;
      for (s = new Array(h), o = new Array(h), l = 0; l < h; ++l)
        o[l] = +i(n[l], l, n), s[l] = isNaN(o[l]) ? 0 : +r(n[l], l, n);
    }
  }
  return a.initialize = function(l) {
    n = l, c();
  }, a.strength = function(l) {
    return arguments.length ? (r = typeof l == "function" ? l : nt(+l), c(), a) : r;
  }, a.radius = function(l) {
    return arguments.length ? (i = typeof l == "function" ? l : nt(+l), c(), a) : i;
  }, a.x = function(l) {
    return arguments.length ? (t = +l, a) : t;
  }, a.y = function(l) {
    return arguments.length ? (e = +l, a) : e;
  }, a;
}
function Er(i) {
  var t = nt(0.1), e, n, r;
  typeof i != "function" && (i = nt(i == null ? 0 : +i));
  function s(a) {
    for (var c = 0, l = e.length, h; c < l; ++c)
      h = e[c], h.vx += (r[c] - h.x) * n[c] * a;
  }
  function o() {
    if (e) {
      var a, c = e.length;
      for (n = new Array(c), r = new Array(c), a = 0; a < c; ++a)
        n[a] = isNaN(r[a] = +i(e[a], a, e)) ? 0 : +t(e[a], a, e);
    }
  }
  return s.initialize = function(a) {
    e = a, o();
  }, s.strength = function(a) {
    return arguments.length ? (t = typeof a == "function" ? a : nt(+a), o(), s) : t;
  }, s.x = function(a) {
    return arguments.length ? (i = typeof a == "function" ? a : nt(+a), o(), s) : i;
  }, s;
}
function Sr(i) {
  var t = nt(0.1), e, n, r;
  typeof i != "function" && (i = nt(i == null ? 0 : +i));
  function s(a) {
    for (var c = 0, l = e.length, h; c < l; ++c)
      h = e[c], h.vy += (r[c] - h.y) * n[c] * a;
  }
  function o() {
    if (e) {
      var a, c = e.length;
      for (n = new Array(c), r = new Array(c), a = 0; a < c; ++a)
        n[a] = isNaN(r[a] = +i(e[a], a, e)) ? 0 : +t(e[a], a, e);
    }
  }
  return s.initialize = function(a) {
    e = a, o();
  }, s.strength = function(a) {
    return arguments.length ? (t = typeof a == "function" ? a : nt(+a), o(), s) : t;
  }, s.y = function(a) {
    return arguments.length ? (i = typeof a == "function" ? a : nt(+a), o(), s) : i;
  }, s;
}
function fn(i, t) {
  let e = [];
  function n() {
    if (!e) return;
    const r = (i - t) * 0.9;
    for (const s of e) {
      if (s.x == null || s.y == null) continue;
      const o = s.x, a = s.y, c = s.getCircleRadius() ?? 10, l = Math.sqrt(o * o + a * a) + c;
      if (l > r) {
        const h = r / l, d = o * h, u = a * h;
        s.x = d, s.y = u;
      }
    }
  }
  return n.initialize = (r) => {
    e = r;
  }, n;
}
class kd {
  /**
   * Convert global coordinates to local coordinates relative to a parent cluster.
   *
   * Used when reading positions from the main graph and applying them to subgraph nodes.
   *
   * @param globalX Global X coordinate
   * @param globalY Global Y coordinate  * @param parentNode The parent cluster node (whose position defines the local origin)
   * @returns Local coordinates relative to parent center
   */
  static globalToLocal(t, e, n) {
    const r = n.x ?? 0, s = n.y ?? 0;
    return {
      x: t - r,
      y: e - s
    };
  }
  /**
   * Convert local coordinates (relative to parent cluster center) to global coordinates.
   *
   * Used when reading positions from subgraph nodes and updating the main graph.
   *
   * @param localX Local X coordinate (relative to parent)
   * @param localY Local Y coordinate (relative to parent)
   * @param parentNode The parent cluster node (whose position defines the local origin)
   * @returns Global coordinates
   */
  static localToGlobal(t, e, n) {
    const r = n.x ?? 0, s = n.y ?? 0;
    return {
      x: t + r,
      y: e + s
    };
  }
}
class it {
  constructor(t) {
    f(this, "nodeDrawer");
    f(this, "edgeDrawer");
    this.nodeDrawer = t;
  }
  /**
   * Renders an expanded cluster with its nested subgraph.
   *
   * This is called when a node with children is expanded. It creates:
   * - A cluster area circle around the parent node
   * - A nested subgraph containing the children nodes
   * - Appropriate edge visibility (hide synthetic, show actual)
   *
   * @param theClusterSelection - D3 selection of the cluster's SVG group element
   * @param node - The node being expanded
   * @param cb - Callback invoked after cluster expansion completes, receives final radius
   * @returns The cluster circle selection
   */
  render(t, e, n) {
    this.edgeDrawer || (this.edgeDrawer = this.nodeDrawer.graphSvgRenderer.edgeDrawer);
    let r = t.select(".pvt-cluster-area");
    if (r.empty()) {
      r = t.append("circle").classed("pvt-cluster-area", !0).lower();
      const d = it.buildGradientForNode(
        t.node().querySelector(".node"),
        r,
        e
      );
      d && r.style("stroke", `color-mix(in srgb, ${d} 70%, transparent)`);
    }
    const s = it.updateToNewRadiusExpanded(this.nodeDrawer.graph, e);
    r.attr("r", 0).attr("_final_r", s).attr("cx", 0).attr("cy", 0), r.transition().duration(250).attr("r", s);
    const o = /* @__PURE__ */ new Set(), a = e.children.flatMap((d) => [
      ...d.getEdgesOut() ?? [],
      ...d.getEdgesIn() ?? []
    ]).filter((d) => o.has(d.id) ? !1 : (o.add(d.id), !0)), c = t.node(), l = this.createSubgraph(
      e.children,
      a,
      c,
      e,
      this.nodeDrawer.graph
    );
    e.setSubgraph(l), t.select(":scope > .zoom-layer").attr("opacity", 0).transition().duration(250).attr("opacity", 1), it.toggleSyntheticEdges(e);
    let h = this.nodeDrawer.graph.getParentGraph();
    for (; h; )
      h.renderer.update(!1), h = h.getParentGraph();
    return n && requestAnimationFrame(() => {
      n(s);
    }), r;
  }
  /**
   * Creates a nested subgraph for rendering children inside a cluster.
   *
   * The subgraph is a separate Graph instance that:
   * - Uses local coordinates (relative to parent cluster center at 0,0)
   * - Contains clones of the child nodes
   * - Shares the same Node object references for proper position syncing
   * - Has its own simulation constrained within the parent radius
   *
   * @param nodes - Child nodes to include in the subgraph
   * @param edges - Edges connecting the child nodes
   * @param container - SVG group element to contain the subgraph
   * @param parentNode - The parent cluster node (defines the local coordinate origin)
   * @param parentGraph - Reference to the parent graph for coordinate conversion
   * @returns The created subgraph instance
   */
  createSubgraph(t, e, n, r, s) {
    const o = (u) => {
      u.getMutableNodes().forEach((p) => {
        let g = s.getMutableNode(p.id);
        g = g.getOriginalObject() ?? g, p.setOriginalObject(g), g.setDeepestNodeClone(p), p.isChild = !0;
      }), u.getMutableEdges().forEach((p) => {
        let g = s.getMutableEdge(p.id);
        g && (g = g.getOriginalObject() ?? g, p.setOriginalObject(g));
      }), t.forEach((p) => {
        var g;
        if (((g = p.parentNode) == null ? void 0 : g.id) === r.id) {
          const v = u.getMutableNode(p.id);
          v && (v.parentNode = r);
        }
      }), s.getMutableEdges().forEach((p) => {
        const g = p.getOriginalObject() ?? p, v = u.getMutableNode(p.from.id), y = u.getMutableNode(p.to.id);
        v && g.setSubgraphFromNode(v), y && g.setSubgraphToNode(y);
      });
    }, a = {
      UI: {
        mode: "viewer",
        tooltip: {
          enabled: !1
        },
        contextMenu: {
          enabled: !1
        },
        navigation: {
          enabled: !1
        }
      },
      render: {
        ...this.nodeDrawer.graph.getOptions().render,
        zoomEnabled: !1,
        zoomAnimationDuration: 100,
        beforeRender: o
      },
      simulation: {
        useWorker: !1,
        warmupTicks: 10,
        cooldownTime: 50,
        freezeNodesOnDrag: !1
      },
      callbacks: {
        onNodeSelect: (u) => {
          const p = s.getMutableNode(u.id);
          p && s.selectElement(p);
        },
        onNodesSelect: (u) => {
          const p = h.renderer.getGraphInteraction().getSelectedNodeIDs();
          if (p === null) return;
          const g = p.map((v) => {
            const y = s.getMutableNode(v);
            return {
              node: y,
              element: y == null ? void 0 : y.getGraphElement()
            };
          });
          s.renderer.getGraphInteraction().addNodesToSelection(g);
        },
        onEdgeSelect: (u) => {
          const p = s.getMutableEdge(u.id);
          p && s.selectElement(p);
        },
        onNodeHoverIn: (u, p) => {
          var g;
          (g = s.UIManager.tooltip) == null || g.openForNodeOnElement(u, p);
        }
      },
      parentGraph: this.nodeDrawer.graph
    }, c = {
      nodes: [...t].map((u) => u.toDict(!0)),
      edges: [...e].map((u) => u.toDict())
    }, l = document.createElement("div"), h = new bt(l, c, a), d = l.querySelector(".zoom-layer");
    return n.appendChild(d), h.getMutableNodes().forEach((u) => {
      it.toggleSyntheticEdges(u);
    }), h.on("ready", () => {
      h.simulation.getSimulation().force("center", Kh(0, 0)).force("constrainParent", fn(r.getCircleRadius(), 10)), h.simulation.restart();
    }), h.renderer.getGraphInteraction().on("dragended", () => {
    }), h.renderer.getGraphInteraction().on("simulationTick", () => {
      h.getMutableNodes().filter((p) => p.visible).forEach((p) => {
        const g = p.x ?? 0, v = p.y ?? 0;
        this.updatePositionOnRealChild(g, v, p.id);
      });
    }), s.renderer.getGraphInteraction().on("dragging", () => {
      this.updatePositionOnAllRealChildren(s);
    }), s.renderer.getGraphInteraction().on("simulationTick", () => {
      this.updatePositionOnAllRealChildren(s);
    }), s.renderer.getGraphInteraction().on("canvasClick", () => {
      h.deselectAll();
    }), h;
  }
  /**
   * Recursively updates positions of all real child nodes across nested subgraphs.
   *
   * This is called during simulation tick and drag events to propagate position changes
   * from subgraphs up to the main graph. It handles nested clusters by recursing through
   * parent graphs.
   *
   * @param graph - The graph to process (can be main graph or subgraph)
   */
  updatePositionOnAllRealChildren(t) {
    t.getMutableNodes().filter((e) => e.isParent && e.expanded).forEach((e) => {
      const n = e.children, r = e.getSubgraph(), s = /* @__PURE__ */ new Map();
      r && (r.getMutableNodes().forEach((o) => {
        s.set(o.id, o);
      }), this.updatePositionOnAllRealChildren(r)), n.forEach((o) => {
        const a = s.get(o.id);
        !a || !a.x || !a.y || this.updatePositionOnRealChild(a.x, a.y, o.id);
      });
    });
  }
  /**
   * Updates the position of a real child node in the main graph based on its subgraph position.
   * Then recursively bubbles the update up to parent graphs.
   *
   * This is the core method for syncing subgraph positions (local coordinates) to the main
   * graph (global coordinates). It:
   * 1. Converts local subgraph position to global position
   * 2. Updates the real node's position in the parent graph
   * 3. Triggers a render tick for the updated node
   * 4. Recursively updates parent graphs if this is a nested subgraph
   *
   * @param x - Local X position of the child in the subgraph
   * @param y - Local Y position of the child in the subgraph
   * @param id - ID of the child node (same in both subgraph and main graph)
   */
  updatePositionOnRealChild(t, e, n) {
    const r = this.nodeDrawer.graph.getMutableNode(n), s = r == null ? void 0 : r.parentNode;
    if (r && s) {
      const o = kd.localToGlobal(t, e, s);
      r.x = o.x, r.y = o.y, this.nodeDrawer.graph.renderer.nextTickFor([r]);
      const a = this.nodeDrawer.graph.getParentGraph();
      a && a.renderer.nodeDrawer.clusterDrawer.updatePositionOnRealChild(t, e, n);
    }
  }
  /**
   * Toggles visibility of synthetic edges based on cluster expansion state.
   *
   * Synthetic edges are placeholder edges created during graph normalization that point
   * from external nodes to collapsed cluster children. When a cluster is expanded:
   * - Synthetic edges pointing to children are hidden
   * - Actual edges within the subgraph are shown
   * When collapsed:
   * - Synthetic edges are shown again
   * - Actual nested edges are hidden
   *
   * @param node - The cluster node being expanded/collapsed
   */
  static toggleSyntheticEdges(t) {
    if (t.expanded) {
      t.getEdgesIn().filter((n) => n.isSynthetic === !0).forEach((n) => {
        n.hide();
      });
      const e = t.getOriginalObject() ?? t;
      e.getEdgesIn().filter((n) => n.isSynthetic === !0).forEach((n) => {
        n.hide();
      }), e.children.forEach((n) => {
        n.getEdgesIn().filter((r) => !e.children.includes(r.from)).forEach((r) => {
          r.show();
        });
      });
    } else {
      t.getEdgesIn().filter((n) => n.isSynthetic === !0).forEach((n) => {
        n.show();
      });
      const e = t.getOriginalObject() ?? t;
      e.getEdgesIn().filter((n) => n.isSynthetic === !0).forEach((n) => {
        t.visible && n.show();
      }), it.hideNestedEdges(e);
    }
  }
  /**
   * Recursively hides edges that point to nested children of a collapsed cluster.
   *
   * When a cluster is collapsed, edges that would point to its nested children
   * need to be hidden since those children are not visible. This method traverses
   * the entire child hierarchy.
   *
   * @param node - The cluster node whose nested edges should be hidden
   */
  static hideNestedEdges(t) {
    t.children.forEach((e) => {
      it.hideNestedEdges(e), e.getEdgesIn().filter((n) => !t.children.includes(n.from)).forEach((n) => {
        n.hide();
      });
    });
  }
  /**
   * Recursively collapses all expanded clusters starting from the given node.
   *
   * Used when collapsing a parent cluster - all nested expanded clusters
   * must also be collapsed first.
   *
   * @param node - The node whose subtree should be collapsed
   */
  static collapseAllOpenedClusters(t) {
    t.children.forEach((e) => {
      it.collapseAllOpenedClusters(e), e.collapse(), e.setCircleRadius(e.getCircleRadiusCollapsed());
    });
  }
  /**
   * Updates the radius of a node when it is expanded, propagating changes up the parent hierarchy.
   *
   * When a cluster node expands:
   * 1. Save current radius as collapsed radius
   * 2. Calculate new expanded radius based on children
   * 3. Update the node in its parent graph
   * 4. Recursively update parent clusters
   *
   * @param graph - The graph containing the node
   * @param node - The node being expanded
   * @returns The calculated expanded radius
   */
  static updateToNewRadiusExpanded(t, e) {
    const n = it.getRadiusForClusterNode(e);
    e.expanded || e.setCircleRadiusCollapsed(e.getCircleRadius()), e.setCircleRadius(n);
    const r = t.getParentGraph();
    if (r) {
      const s = it.updateParentGraph(r, e, n);
      s && t.simulation.getSimulation().force("link", null).force("constrainParent", fn(s, 10)), r.getParentGraph() && e.parentNode && it.updateToNewRadiusExpanded(r, e.parentNode);
    }
    return n;
  }
  /**
   * Updates the radius of a node when it is collapsed, propagating changes up the parent hierarchy.
   *
   * @param node - The node being collapsed
   * @param restoreR - Whether to restore the original collapsed radius
   * @param graph - The graph containing the node (optional, used for propagation)
   */
  static updateToNewRadiusCollapsed(t, e, n) {
    const r = e ? t.getCircleRadiusCollapsed() : it.getRadiusForClusterNode(t);
    if (t.setCircleRadius(r), n) {
      it.updateParentGraph(n, t, r);
      const s = n.getParentGraph();
      t.parentNode && it.updateToNewRadiusCollapsed(t.parentNode, !1, s);
    }
  }
  /**
   * Calculates the appropriate radius for a cluster node based on its expansion state.
   *
   * For collapsed nodes: returns current radius + 4px padding
   * For expanded nodes: calculates radius based on children count and sizes using
   * a formula that approximates the area needed to contain all children.
   *
   * @param node - The cluster node to calculate radius for
   * @returns The calculated radius
   */
  static getRadiusForClusterNode(t) {
    if (!t.expanded)
      return t.getCircleRadius() + 4;
    const e = 50, n = 16, s = t.children.reduce((a, c) => {
      const l = c.getCircleRadius();
      return a + l + n;
    }, 0) / t.children.length, o = Math.sqrt(t.children.length) * (2 * s) + e;
    return Math.max(50, o);
  }
  /**
   * Updates the parent graph when a child cluster's radius changes.
   *
   * This method:
   * 1. Updates the radius of the node in the parent graph
   * 2. Triggers a re-layout of the parent graph
   * 3. Updates the parent cluster's visual radius if it exists
   *
   * @param parentGraph - The parent graph to update
   * @param node - The node whose radius changed
   * @param r - The new radius
   * @returns The parent's new radius if updated, undefined otherwise
   */
  static updateParentGraph(t, e, n) {
    var a;
    const r = t.getMutableNode(e.id);
    r == null || r.setCircleRadius(n);
    const s = e.getOriginalObject();
    s && s.setCircleRadius(n);
    const o = e.parentNode;
    if (o) {
      const c = it.getRadiusForClusterNode(o);
      o.setCircleRadius(c), t.onChange(), t.simulation.reheat(0.1);
      const l = (a = o.getGraphElement()) == null ? void 0 : a.querySelector("& > .pvt-cluster-area");
      if (l) {
        const h = tt(l);
        h.attr("_final_r", c).transition().duration(250).attr("r", c), wi.handleChildrenExpanded(t, o, h);
      }
      return c;
    }
  }
  /**
   * Creates a radial gradient fill for the cluster area circle.
   *
   * The gradient fades from transparent at 90% to a color-mixed version of the
   * parent node's fill color at 100%, creating a subtle visual boundary.
   *
   * @param parentCircleElement - The parent node's circle element
   * @param clusterSelection - The cluster area circle selection
   * @param node - The cluster node
   * @returns The parent node's fill color, or undefined if not found
   */
  static buildGradientForNode(t, e, n) {
    if (t) {
      const r = getComputedStyle(t).fill, s = `color-mix(in srgb, ${r} 40%, transparent)`, o = `pvt-cluster-area-${n.id}`, a = t.closest(".pvt-canvas-element"), c = a == null ? void 0 : a.querySelector("defs");
      if (!c) return;
      const l = c.appendChild(document.createElementNS("http://www.w3.org/2000/svg", "radialGradient"));
      l.setAttribute("id", o);
      const h = document.createElementNS("http://www.w3.org/2000/svg", "stop");
      h.setAttribute("offset", "90%"), h.setAttribute("stop-color", "#ffffff00"), l.appendChild(h);
      const d = document.createElementNS("http://www.w3.org/2000/svg", "stop");
      return d.setAttribute("offset", "100%"), d.setAttribute("stop-color", s), l.appendChild(d), e.style("fill", `url(#${o})`), r;
    }
  }
}
tt.prototype.transition = In;
class wi {
  constructor(t, e, n) {
    f(this, "graph");
    f(this, "rendererOptions");
    f(this, "graphSvgRenderer");
    f(this, "clusterDrawer");
    f(this, "renderCB");
    var r;
    this.graphSvgRenderer = n, this.graph = e, this.rendererOptions = t, this.renderCB = (r = this.rendererOptions) == null ? void 0 : r.renderNode, this.clusterDrawer = new it(this);
  }
  render(t, e) {
    var n, r;
    if (this.renderCB) {
      const s = t.append("foreignObject"), o = (n = this == null ? void 0 : this.renderCB) == null ? void 0 : n.call(this, e);
      s.attr("width", 20).attr("height", 20), typeof o == "string" ? s.text(o) : o instanceof HTMLElement && ((r = s.node()) == null || r.append(o)), requestAnimationFrame(() => {
        const a = s.node();
        if (!a) return;
        const c = a.firstElementChild;
        if (!c) return;
        const l = c.getBoundingClientRect(), h = Math.ceil(l.width), d = Math.ceil(l.height);
        s.attr("width", h).attr("height", d), s.attr("x", -h / 2).attr("y", -d / 2), this.rendererOptions.enableNodeExpansion && (!e.hasChildren() || !e.expanded) && e.setCircleRadius(0.5 * Math.max(h, d));
      });
    } else
      this.defaultNodeRender(t, e), requestAnimationFrame(() => {
        const s = t.node();
        if (!s) return;
        let o = 50, a = 50;
        const c = s.getBBox();
        c.width > 0 && c.height > 0 && (o = Math.ceil(c.width), a = Math.ceil(c.height)), this.rendererOptions.enableNodeExpansion && (!e.hasChildren() || !e.expanded) && (this.getNodeStyle(e).shape == "square" ? e.setCircleRadius(Math.SQRT1_2 * Math.max(o, a)) : e.setCircleRadius(0.5 * Math.max(o, a)));
      });
    if (this.rendererOptions.enableNodeExpansion && e.hasChildren()) {
      if (e.expanded) {
        const s = this.clusterDrawer.render(t, e, () => {
          wi.handleChildrenExpanded(this.graph, e, s);
        });
        requestAnimationFrame(() => {
          it.updateToNewRadiusExpanded(this.graph, e);
        });
      }
      requestAnimationFrame(() => {
        this.addExpandCollapseIcons(t, e);
      });
    }
  }
  updatePositions(t) {
    t.attr("transform", (e) => {
      const n = e.x && isFinite(e.x) ? e.x : 0, r = e.y && isFinite(e.y) ? e.y : 0;
      return `translate(${n},${r})`;
    });
  }
  defaultNodeRender(t, e) {
    const n = this.getNodeStyle(e);
    this.genericNodeRender(t, n, e);
  }
  mergeNodeStylingOptions(t) {
    return {
      shape: (t == null ? void 0 : t.shape) ?? this.rendererOptions.defaultNodeStyle.shape,
      strokeColor: (t == null ? void 0 : t.strokeColor) ?? this.rendererOptions.defaultNodeStyle.strokeColor,
      strokeWidth: (t == null ? void 0 : t.strokeWidth) ?? this.rendererOptions.defaultNodeStyle.strokeWidth,
      fontFamily: (t == null ? void 0 : t.fontFamily) ?? this.rendererOptions.defaultNodeStyle.fontFamily,
      size: (t == null ? void 0 : t.size) ?? this.rendererOptions.defaultNodeStyle.size,
      color: (t == null ? void 0 : t.color) ?? this.rendererOptions.defaultNodeStyle.color,
      textColor: (t == null ? void 0 : t.textColor) ?? this.rendererOptions.defaultNodeStyle.textColor,
      textVerticalShift: (t == null ? void 0 : t.textVerticalShift) ?? this.rendererOptions.defaultNodeStyle.textVerticalShift,
      iconUnicode: (t == null ? void 0 : t.iconUnicode) ?? this.rendererOptions.defaultNodeStyle.iconUnicode,
      iconClass: (t == null ? void 0 : t.iconClass) ?? this.rendererOptions.defaultNodeStyle.iconClass,
      svgIcon: (t == null ? void 0 : t.svgIcon) ?? this.rendererOptions.defaultNodeStyle.svgIcon,
      imagePath: (t == null ? void 0 : t.imagePath) ?? this.rendererOptions.defaultNodeStyle.imagePath,
      text: (t == null ? void 0 : t.text) ?? this.rendererOptions.defaultNodeStyle.text,
      html: (t == null ? void 0 : t.html) ?? this.rendererOptions.defaultNodeStyle.html
    };
  }
  computeNodeStyle(t) {
    let e = {};
    if (this.rendererOptions.nodeStyleMap && typeof this.rendererOptions.nodeTypeAccessor == "function") {
      const s = this.rendererOptions.nodeTypeAccessor(t);
      s && (e = this.rendererOptions.nodeStyleMap[s] ?? {});
    }
    const n = t.getStyle();
    let r = {};
    return n.styleCb ? r = n.styleCb(t) : r = {
      shape: (n == null ? void 0 : n.shape) ?? (e == null ? void 0 : e.shape),
      strokeColor: (n == null ? void 0 : n.strokeColor) ?? (e == null ? void 0 : e.strokeColor),
      strokeWidth: (n == null ? void 0 : n.strokeWidth) ?? (e == null ? void 0 : e.strokeWidth),
      fontFamily: (n == null ? void 0 : n.fontFamily) ?? (e == null ? void 0 : e.fontFamily),
      size: (n == null ? void 0 : n.size) ?? (e == null ? void 0 : e.size),
      color: (n == null ? void 0 : n.color) ?? (e == null ? void 0 : e.color),
      textColor: (n == null ? void 0 : n.textColor) ?? (e == null ? void 0 : e.textColor),
      textVerticalShift: (n == null ? void 0 : n.textVerticalShift) ?? (e == null ? void 0 : e.textVerticalShift),
      iconUnicode: (n == null ? void 0 : n.iconUnicode) ?? (e == null ? void 0 : e.iconUnicode),
      iconClass: (n == null ? void 0 : n.iconClass) ?? (e == null ? void 0 : e.iconClass),
      svgIcon: (n == null ? void 0 : n.svgIcon) ?? (e == null ? void 0 : e.svgIcon),
      imagePath: (n == null ? void 0 : n.imagePath) ?? (e == null ? void 0 : e.imagePath),
      text: (n == null ? void 0 : n.text) ?? (e == null ? void 0 : e.text),
      html: (n == null ? void 0 : n.html) ?? (e == null ? void 0 : e.html)
    }, this.mergeNodeStylingOptions(r);
  }
  getNodeStyle(t) {
    const e = this.computeNodeStyle(t);
    return typeof e.shape == "function" && (e.shape = e.shape(t)), e.strokeWidth = e.strokeWidth !== void 0 ? st(e.strokeWidth.toString(), t) ?? "var(--pvt-node-stroke-width, 2)" : "var(--pvt-node-stroke-width, 2)", e.strokeColor = e.strokeColor !== void 0 ? st(e.strokeColor, t) ?? "var(--pvt-node-stroke, #fff)" : "var(--pvt-node-stroke, #fff)", e.size = e.size !== void 0 ? ri(e.size, t) ?? 10 : 10, e.color = e.color !== void 0 ? st(e.color, t) ?? "var(--pvt-node-color, #007acc)" : "var(--pvt-node-color, #007acc)", e.textColor = e.textColor !== void 0 ? st(e.textColor, t) ?? "var(--pvt-node-text-color, #fff)" : "var(--pvt-node-text-color, #fff)", e.textVerticalShift = e.textVerticalShift !== void 0 ? ri(e.textVerticalShift, t) ?? 0 : 0, e.text = e.text !== void 0 ? st(e.text, t) : void 0, e.iconUnicode = e.iconUnicode !== void 0 ? st(e.iconUnicode, t) : void 0, e.iconClass = e.iconClass !== void 0 ? st(e.iconClass, t) : void 0, e.svgIcon = e.svgIcon !== void 0 ? st(e.svgIcon, t) : void 0, e.imagePath = e.imagePath !== void 0 ? st(e.imagePath, t) : void 0, e;
  }
  isCustomShape(t) {
    return typeof t == "object" && t !== null && "d" in t;
  }
  genericNodeRender(t, e, n) {
    var o, a;
    e.size = e.size, e.shape = e.shape, e.text = e.text, e.textVerticalShift = e.textVerticalShift;
    let r = e.shape;
    e.shape == "square" ? r = "rect" : (this.isCustomShape(e.shape) || ["triangle", "hexagon"].includes(e.shape)) && (r = "path");
    const s = t.append(r).attr("stroke", e.strokeColor).attr("stroke-width", e.strokeWidth).attr("fill", e.color).classed("node", !0);
    switch (e.shape) {
      case "circle":
        s.attr("r", e.size), n.setCircleRadius(e.size);
        break;
      case "square":
        s.attr("width", e.size * 2).attr("height", e.size * 2).attr("x", -e.size).attr("y", -e.size), n.setCircleRadius(Math.SQRT1_2 * e.size);
        break;
      case "triangle": {
        const c = [
          [0, -e.size],
          [e.size, e.size],
          [-e.size, e.size]
        ].map((l) => l.join(",")).join(" ");
        s.attr("d", `M${c}Z`), n.setCircleRadius(e.size);
        break;
      }
      case "hexagon": {
        const c = Math.PI / 3, l = Array.from({ length: 6 }, (h, d) => {
          const u = c * d;
          return [Math.cos(u) * e.size, Math.sin(u) * e.size];
        }).map((h) => h.join(",")).join(" ");
        s.attr("d", `M${l}Z`), n.setCircleRadius(e.size);
        break;
      }
      default:
        this.isCustomShape(e.shape) ? (s.attr("d", e.shape.d), n.setCircleRadius(15)) : (s.attr("r", e.size), n.setCircleRadius(e.size));
        break;
    }
    if (e.iconUnicode || e.iconClass)
      t.append("text").attr("fill", e.textColor).attr("text-anchor", "middle").attr("dominant-baseline", "central").attr("font-size", e.size * 1.2).attr("class", "node-content icon " + (e.iconUnicode ? "icon-unicode" : e.iconClass ?? "")).text(e.iconUnicode ?? ts(e.iconClass ?? "") ?? "☐");
    else if (e.svgIcon) {
      const c = document.createElementNS("http://www.w3.org/2000/svg", "svg");
      c.innerHTML = e.svgIcon, ((o = c.children[0]) == null ? void 0 : o.nodeName) === "svg" && (c.children[0].removeAttribute("width"), c.children[0].removeAttribute("height")), t.append(() => c).attr("class", "node-content").attr("x", -e.size * 0.7).attr("y", -e.size * 0.7).attr("width", e.size * 1.4).attr("height", e.size * 1.4).attr("color", e.strokeColor);
    } else if (e.imagePath)
      t.append("image").attr("class", "node-content").attr("xlink:href", e.imagePath).attr("x", -e.size * (1.2 / 2)).attr("y", -e.size * (1.2 / 2)).attr("width", e.size * 1.2).attr("height", e.size * 1.2);
    else if (e.html) {
      const c = t.append("foreignObject"), l = e.html(n);
      c.attr("width", e.size * 2).attr("height", e.size * 2).attr("x", -e.size).attr("y", -e.size), typeof l == "string" ? c.text(l) : l instanceof HTMLElement && ((a = c.node()) == null || a.append(l));
    }
    if (e.text) {
      const [c, l] = this.computeTextLayout(e.text, e.size, e.textVerticalShift);
      t.append("text").attr("text-anchor", "middle").attr("y", -e.textVerticalShift * (e.size + c / 2 * 1.2)).attr("dominant-baseline", "central").attr("font-size", c).attr("font-family", e.fontFamily).attr("fill", e.textColor).text(l);
    }
  }
  checkForHighlight(t, e) {
    this.isNodeSelected(e) ? this.highlightSelection(t, e) : this.deHighlightSelection(t, e);
  }
  isNodeSelected(t) {
    var a;
    const e = this.graphSvgRenderer.getGraphInteraction(), n = e.getSelectedNode(), r = e.getSelectedNodeIDs(), s = ((a = n == null ? void 0 : n.node) == null ? void 0 : a.id) === t.id, o = Array.isArray(r) ? r.includes(t.id) : !1;
    return s || o;
  }
  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  deHighlightSelection(t, e) {
    t.classed("pvt-node-selected-highlight", !1), this.rendererOptions.enableFocusMode && (this.graph.getMutableNodes().forEach((n) => {
      const r = n.getGraphElement();
      r == null || r.classList.toggle("pvt-node-selected-highlight-shadow", !1);
    }), this.graph.getMutableEdges().forEach((n) => {
      const r = n.getGraphElement();
      r == null || r.classList.toggle("pvt-edge-selected-highlight-shadow", !1);
    }));
  }
  highlightSelection(t, e) {
    this.rendererOptions.enableFocusMode && (this.graph.getMutableNodes().forEach((n) => {
      const r = n.getGraphElement();
      r == null || r.classList.toggle("pvt-node-selected-highlight-shadow", !0);
    }), this.graph.getMutableEdges().forEach((n) => {
      const r = n.getGraphElement();
      r == null || r.classList.toggle("pvt-edge-selected-highlight-shadow", !0);
    }), t.classed("pvt-node-selected-highlight-shadow", !1)), t.classed("pvt-node-selected-highlight", !0), this.rendererOptions.enableFocusMode && (e.getEdgesOut().forEach((n) => {
      const r = n.getGraphElement();
      r == null || r.classList.toggle("pvt-edge-selected-highlight-shadow", !1);
      const s = n.to.getGraphElement();
      s == null || s.classList.toggle("pvt-node-selected-highlight-shadow", !1);
    }), e.getEdgesIn().forEach((n) => {
      const r = n.getGraphElement();
      r == null || r.classList.toggle("pvt-edge-selected-highlight-shadow", !1);
      const s = n.from.getGraphElement();
      s == null || s.classList.toggle("pvt-node-selected-highlight-shadow", !1);
    }));
  }
  computeTextLayout(t, e, n = 0) {
    const r = e * 0.9, s = Math.abs(n) >= 1 ? r * 6 : r * 2, o = r * 0.5, a = r * 0.5, c = Math.floor(s / a);
    if (t.length > c && t.length > 7) {
      const l = Math.max(6, s / a) - 1, h = Math.min(3, Math.floor(l / 2)), d = l - h;
      t = t.slice(0, d) + "..." + t.slice(t.length - h);
    }
    return [o, t];
  }
  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  addExpandCollapseIcons(t, e) {
    const s = (o, a) => {
      this.graph.UIManager.tooltip && this.graph.UIManager.tooltip.hide(o), this.graph.toggleExpandNode(o), a || (this.graph.simulation.reheat(0.05), this.graph.renderer.fitAndCenter());
    };
    t.each((o, a, c) => {
      const l = tt(c[a]);
      l.selectAll(":scope > .node-icon").remove();
      const h = (o.getCircleRadius() + 2) / Math.sqrt(2), d = l.append("g").classed("node-icon", !0).classed(o.expanded ? "collapse-icon" : "expand-icon", !0).attr("transform", o.expanded ? `translate(${h}, ${h})` : `translate(${h}, ${-h})`);
      d.append("title").text(o.expanded ? "Collapse nodes" : "Expand node"), d.append("circle").attr("r", 8).style("cursor", "pointer").on("click", (u) => {
        u.stopPropagation(), s(o, !o.expanded);
      }), l.select(o.expanded ? ":scope > .collapse-icon" : ":scope > .expand-icon").append("text").text(o.expanded ? "-" : "+");
    });
  }
  static handleChildrenExpanded(t, e, n) {
    var h, d;
    t.simulation.reheat(0.1);
    const r = Number(n.attr("_final_r")), o = (r + 2) / Math.sqrt(2), a = (h = e.getGraphElement()) == null ? void 0 : h.querySelector("& > .node");
    a && tt(a).transition().duration(250).on("end", () => {
      t.renderer.fitAndCenter();
    }).attr("transform", `translate(${-o}, ${-o})`);
    const c = (d = e.getGraphElement()) == null ? void 0 : d.querySelector("& > .node-icon");
    c && tt(c).transition().duration(250).attr("transform", e.expanded ? `translate(${o}, ${o})` : `translate(${o}, ${-o})`);
    const l = e.getSubgraph();
    l && l.simulation.getSimulation().force("constrainParent", fn(Number(r), 10));
  }
}
function Nd(i) {
  return i * Math.PI / 180;
}
function ye(i) {
  for (; i < 0; ) i += 2 * Math.PI;
  for (; i >= 2 * Math.PI; ) i -= 2 * Math.PI;
  return i;
}
function Ad(i) {
  let { rx: t, ry: e } = i;
  const { xAxisRotation: n, from: r, to: s } = i, o = Nd(n), a = Math.cos(o), c = Math.sin(o), l = (r.x - s.x) / 2, h = (r.y - s.y) / 2, d = a * l + c * h, u = -c * l + a * h;
  let p = t * t, g = e * e;
  const v = d * d, y = u * u, b = v / p + y / g;
  if (b > 1) {
    const O = Math.sqrt(b);
    t *= O, e *= O, p = t * t, g = e * e;
  }
  const x = 1, S = p * g - p * y - g * v, C = p * y + g * v, N = x * Math.sqrt(Math.max(0, S / C)), P = N * (t * u / e), k = N * (-(e * d) / t), A = a * P - c * k + (r.x + s.x) / 2, I = c * P + a * k + (r.y + s.y) / 2;
  function z(O, B, R, H) {
    const V = O * R + B * H, j = Math.sqrt(O * O + B * B) * Math.sqrt(R * R + H * H);
    let $ = Math.acos(Math.min(Math.max(V / j, -1), 1));
    return O * H - B * R < 0 && ($ = -$), $;
  }
  const F = (d - P) / t, Z = (u - k) / e, Q = (-d - P) / t, E = (-u - k) / e;
  let L = z(1, 0, F, Z), _ = z(F, Z, Q, E);
  return _ < 0 && (_ += 2 * Math.PI), L = ye(L), _ = ye(_), {
    cx: A,
    cy: I,
    startAngle: L,
    deltaAngle: _,
    rx: t,
    ry: e,
    xAxisRotation: n
  };
}
function Id(i, t, e, n, r, s) {
  const o = n - i, a = r - t, c = Math.sqrt(o * o + a * a);
  if (c > e + s) return [];
  if (c < Math.abs(e - s)) return [];
  if (c === 0 && e === s) return [];
  const l = (e * e - s * s + c * c) / (2 * c), h = Math.sqrt(e * e - l * l), d = i + l * o / c, u = t + l * a / c, p = d + h * a / c, g = u - h * o / c, v = d - h * a / c, y = u + h * o / c;
  return h === 0 ? [{ x: p, y: g }] : [
    { x: p, y: g },
    { x: v, y }
  ];
}
function Ld(i, t, e) {
  i = ye(i), t = ye(t);
  const n = ye(t + e);
  return e >= 0 ? t <= n ? i >= t && i <= n : i >= t || i <= n : n <= t ? i <= t && i >= n : i <= t || i >= n;
}
function Od(i, t) {
  const { cx: e, cy: n, startAngle: r, deltaAngle: s } = t;
  for (const o of i) {
    const a = Math.atan2(o.y - n, o.x - e);
    if (Ld(a, r, s))
      return o;
  }
  return null;
}
function _r(i, t) {
  const e = Ad(i);
  if (e.rx === e.ry && e.xAxisRotation === 0) {
    const n = Id(
      e.cx,
      e.cy,
      e.rx,
      t.cx,
      t.cy,
      t.r
    ), r = Od(n, e);
    return r || null;
  } else
    return console.log("Arc is elliptical or rotated, numerical methods needed for intersection."), null;
}
function Td(i) {
  if (!i) return null;
  const t = i.getAttribute("d");
  if (!t) return null;
  const e = Bd(t);
  if (!e) return null;
  const { x0: n, y0: r, x1: s, y1: o } = e, a = s - n, c = o - r, l = {
    x: n + a / 2,
    y: r + c / 2
  };
  return {
    length: Math.sqrt(a * a + c * c),
    midpoint: l
  };
}
function Pd(i) {
  if (!i) return null;
  const t = i.getAttribute("d");
  if (!t) return null;
  const e = Fd(t);
  if (!e) return null;
  const n = e.to.x - e.from.x, r = e.to.y - e.from.y, s = Math.hypot(n, r), o = e.rx, a = 2 * Math.asin(Math.min(s / (2 * o), 1)), c = o * a, l = (e.from.x + e.to.x) / 2, h = (e.from.y + e.to.y) / 2, d = Math.sqrt(Math.max(0, o * o - (s / 2) ** 2)), u = -r / s, p = n / s, g = e.sweepFlag !== e.largeArcFlag ? 1 : -1, v = l + g * d * u, y = h + g * d * p, b = Math.atan2(e.from.y - y, e.from.x - v);
  let S = Math.atan2(e.to.y - y, e.to.x - v) - b;
  for (; S > Math.PI; ) S -= 2 * Math.PI;
  for (; S < -Math.PI; ) S += 2 * Math.PI;
  e.sweepFlag && S < 0 && (S += 2 * Math.PI), !e.sweepFlag && S > 0 && (S -= 2 * Math.PI);
  const C = b + S / 2, N = {
    x: v + o * Math.cos(C),
    y: y + o * Math.sin(C)
  };
  return {
    length: c,
    midpoint: N
  };
}
function Dd(i) {
  if (!i) return null;
  const t = i.getAttribute("d");
  if (!t) return null;
  const e = zd(t);
  if (!e) return null;
  const n = 0.5, r = Math.pow(1 - n, 3) * e.x0 + 3 * Math.pow(1 - n, 2) * n * e.px0 + 3 * (1 - n) * n * n * e.px1 + n * n * n * e.x1, s = Math.pow(1 - n, 3) * e.y0 + 3 * Math.pow(1 - n, 2) * n * e.py0 + 3 * (1 - n) * n * n * e.py1 + n * n * n * e.y1;
  return { length: Math.hypot(r, s), midpoint: { x: r, y: s } };
}
function Fd(i) {
  if (!i) return null;
  const t = Tn(i);
  return t.length !== 9 || t[0][0] !== "M" || t[2][0] !== "A" ? null : {
    from: { x: parseFloat(t[0].slice(1)), y: parseFloat(t[1]) },
    to: { x: parseFloat(t[7]), y: parseFloat(t[8]) },
    rx: parseFloat(t[2].slice(1)),
    ry: parseFloat(t[3]),
    xAxisRotation: 0,
    largeArcFlag: !1,
    sweepFlag: !0
  };
}
function zd(i) {
  if (!i) return null;
  const t = Tn(i);
  return t.length !== 10 || t[0][0] !== "M" || t[3][0] !== "C" ? null : {
    x0: parseFloat(t[1]),
    y0: parseFloat(t[2]),
    x1: parseFloat(t[8]),
    y1: parseFloat(t[9]),
    px0: parseFloat(t[4]),
    py0: parseFloat(t[5]),
    px1: parseFloat(t[6]),
    py1: parseFloat(t[7])
  };
}
function Bd(i) {
  if (!i) return null;
  const t = Tn(i);
  return t.length !== 6 || t[0] !== "M" || t[3] !== "L" ? null : {
    x0: parseFloat(t[1]),
    y0: parseFloat(t[2]),
    x1: parseFloat(t[4]),
    y1: parseFloat(t[5])
  };
}
function Tn(i) {
  const t = [];
  let e = "", n = 0, r = i.length - 1;
  for (; n <= r && (i[n] === " " || i[n] === `
` || i[n] === "	" || i[n] === ","); ) n++;
  for (; r >= n && (i[r] === " " || i[r] === `
` || i[r] === "	" || i[r] === ","); ) r--;
  for (let s = n; s <= r; s++) {
    const o = i[s];
    o === " " || o === "," || o === `
` || o === "	" ? e && (t.push(e), e = "") : e += o;
  }
  return e && t.push(e), t;
}
function Wt(i, t) {
  var n;
  if (t.nodeHeaderMap.title)
    return st(t.nodeHeaderMap.title, i) || "Could not resolve title";
  const e = (n = i.getData()) == null ? void 0 : n.label;
  return typeof e == "string" ? e : "Optional name or label";
}
function As(i, t) {
  var n;
  if (t.nodeHeaderMap.subtitle)
    return st(t.nodeHeaderMap.subtitle, i) || null;
  const e = (n = i.getData()) == null ? void 0 : n.description;
  return typeof e == "string" ? e : "Optional subtitle or description";
}
function be(i, t) {
  var n;
  if (t.edgeHeaderMap.title)
    return st(t.edgeHeaderMap.title, i) || "";
  const e = (n = i.getData()) == null ? void 0 : n.label;
  return typeof e == "string" ? e : "Optional name or label";
}
function Is(i, t) {
  var n;
  if (t.edgeHeaderMap.subtitle)
    return st(t.edgeHeaderMap.subtitle, i) || null;
  const e = (n = i.getData()) == null ? void 0 : n.label;
  return typeof e == "string" ? e : "Optional subtitle or description";
}
function Ls(i) {
  var e;
  const t = (e = i.getData()) == null ? void 0 : e.label;
  return typeof t == "string" ? t : "";
}
function gn(i, t) {
  const e = i.getData(), n = [];
  if (t.nodePropertiesMap)
    return Jr(t.nodePropertiesMap, i);
  for (const [r, s] of Object.entries(e))
    r && s && n.push({
      name: r,
      value: s
    });
  return n;
}
function mn(i, t) {
  const e = i.getData(), n = [];
  if (t.edgePropertiesMap)
    return Jr(t.edgePropertiesMap, i);
  for (const [r, s] of Object.entries(e))
    r && s && n.push({
      name: r,
      value: s
    });
  return n;
}
class Rd {
  constructor(t, e, n) {
    f(this, "graph");
    f(this, "rendererOptions");
    f(this, "graphSvgRenderer");
    f(this, "renderLabelCB");
    var r;
    this.graphSvgRenderer = n, this.graph = e, this.rendererOptions = t, this.renderLabelCB = (r = this.rendererOptions) == null ? void 0 : r.renderLabel;
  }
  render(t, e) {
    this.defaultEdgeRender(t, e);
  }
  defaultEdgeRender(t, e) {
    var s, o;
    const n = this.getEdgeStyle(e), r = this.getLabelStyle(e);
    if (this.graph.getOptions().isDirected || e.directed) {
      const a = this.genericEdgeRender(t, n);
      this.drawEdgeMarker(a, n, e);
    }
    if (this.renderLabelCB) {
      const a = t.append("g").classed("label-container", !0).append("foreignObject"), c = (s = this == null ? void 0 : this.renderLabelCB) == null ? void 0 : s.call(this, e);
      a.attr("width", 200).attr("height", 100), typeof c == "string" ? a.text(c) : c instanceof HTMLElement && ((o = a.node()) == null || o.append(c)), requestAnimationFrame(() => {
        const l = a.node();
        if (!l) return;
        const h = l.firstElementChild;
        if (!h) return;
        const d = h.getBoundingClientRect(), u = Math.ceil(d.width), p = Math.ceil(d.height);
        a.attr("width", u).attr("height", p), a.attr("x", -u / 2).attr("y", -p / 2), this.highlightSelection(t, e);
      });
    } else
      this.defaultLabelRender(t, e, r), this.highlightSelection(t, e);
  }
  getLabelStyle(t) {
    var r, s, o, a;
    let e;
    const n = t.getLabelStyle();
    return n && n.styleCb ? e = n.styleCb(t) : e = {
      backgroundColor: (r = t.getLabelStyle()) == null ? void 0 : r.backgroundColor,
      fontSize: (s = t.getLabelStyle()) == null ? void 0 : s.fontSize,
      fontFamily: (o = t.getLabelStyle()) == null ? void 0 : o.fontFamily,
      color: (a = t.getLabelStyle()) == null ? void 0 : a.color
    }, this.mergeLabelStylingOptions(e);
  }
  mergeLabelStylingOptions(t) {
    return {
      backgroundColor: (t == null ? void 0 : t.backgroundColor) ?? this.rendererOptions.defaultLabelStyle.backgroundColor,
      fontSize: (t == null ? void 0 : t.fontSize) ?? this.rendererOptions.defaultLabelStyle.fontSize,
      fontFamily: (t == null ? void 0 : t.fontFamily) ?? this.rendererOptions.defaultLabelStyle.fontFamily,
      color: (t == null ? void 0 : t.color) ?? this.rendererOptions.defaultLabelStyle.color
    };
  }
  getEdgeStyle(t) {
    var s;
    let e;
    const n = t.getEdgeStyle();
    n && n.styleCb ? e = n.styleCb(t) : e = {
      strokeColor: n == null ? void 0 : n.strokeColor,
      strokeWidth: n == null ? void 0 : n.strokeWidth,
      opacity: n == null ? void 0 : n.opacity,
      curveStyle: n == null ? void 0 : n.curveStyle,
      dashed: n == null ? void 0 : n.dashed,
      animateDash: n == null ? void 0 : n.animateDash,
      rotateLabel: n == null ? void 0 : n.rotateLabel,
      markerEnd: n == null ? void 0 : n.markerEnd,
      markerStart: n == null ? void 0 : n.markerStart
    };
    const r = this.mergeEdgeStylingOptions(e);
    if (r.strokeColor = r.strokeColor !== void 0 ? st(r.strokeColor, t) ?? "var(--pvt-edge-stroke, #999)" : "var(--pvt-edge-stroke, #999)", r.strokeWidth = r.strokeWidth !== void 0 ? ri(r.strokeWidth, t) ?? 2 : 2, r.opacity = r.opacity !== void 0 ? ri(r.opacity, t) ?? 1 : 1, r.curveStyle = r.curveStyle !== void 0 ? st(r.curveStyle, t) : "bidirectional", r.markerEnd = r.markerEnd !== void 0 ? st(r.markerEnd, t) : void 0, r.markerStart = r.markerStart !== void 0 ? st(r.markerStart, t) : void 0, r.dashed = r.dashed !== void 0 ? ni(r.dashed, t) : void 0, r.animateDash = r.animateDash !== void 0 ? ni(r.animateDash, t) : void 0, t.to.parentNode && t.to.parentNode === t.from) {
      r.curveStyle = "straight";
      const a = (s = (t.getSubgraphFromNode() ?? t.from).getGraphElement()) == null ? void 0 : s.querySelector(".node");
      a && (r.strokeColor = getComputedStyle(a).fill, r.markerStart = "bigcircle", r.markerEnd = "arrow");
    }
    return r;
  }
  mergeEdgeStylingOptions(t) {
    return {
      strokeColor: (t == null ? void 0 : t.strokeColor) ?? this.rendererOptions.defaultEdgeStyle.strokeColor,
      strokeWidth: (t == null ? void 0 : t.strokeWidth) ?? this.rendererOptions.defaultEdgeStyle.strokeWidth,
      opacity: (t == null ? void 0 : t.opacity) ?? this.rendererOptions.defaultEdgeStyle.opacity,
      curveStyle: (t == null ? void 0 : t.curveStyle) ?? this.rendererOptions.defaultEdgeStyle.curveStyle,
      dashed: (t == null ? void 0 : t.dashed) ?? this.rendererOptions.defaultEdgeStyle.dashed,
      animateDash: (t == null ? void 0 : t.animateDash) ?? this.rendererOptions.defaultEdgeStyle.animateDash,
      rotateLabel: (t == null ? void 0 : t.rotateLabel) ?? this.rendererOptions.defaultEdgeStyle.rotateLabel,
      markerEnd: (t == null ? void 0 : t.markerEnd) ?? this.rendererOptions.defaultEdgeStyle.markerEnd,
      markerStart: (t == null ? void 0 : t.markerStart) ?? this.rendererOptions.defaultEdgeStyle.markerStart
    };
  }
  genericEdgeRender(t, e) {
    const n = t.append("path").attr("stroke", e.strokeColor ?? "var(--pvt-edge-stroke)").attr("stroke-width", e.strokeWidth ?? "var(--pvt-edge-stroke-width)").attr("stroke-opacity", e.opacity);
    return e.dashed && (n.classed("dashed", !0), e.animateDash && n.classed("animated", !0)), n;
  }
  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  drawEdgeMarker(t, e, n) {
    if (!this.rendererOptions.markerStyleMap)
      return;
    const r = e.markerEnd, s = e.markerStart;
    r && this.rendererOptions.markerStyleMap[r] && t.attr("marker-end", `url(#${r})`), s && this.rendererOptions.markerStyleMap[s] && t.attr("marker-start", `url(#${s})`);
  }
  updatePositions(t) {
    const e = t.selectAll("path"), n = t.selectAll("g.label-container");
    e.attr("d", (r) => this.linkPathRouter(r)), n.attr("transform", (r, s, o) => {
      const { from: a, to: c } = r, l = this.getEdgeStyle(r), h = o[s].parentNode;
      let d = null;
      h && h instanceof Element && (d = tt(h).select("path").node());
      let u, p, g = { x: 0, y: 0 }, v = 0;
      if (a === c) {
        const y = d ? Dd(d) : void 0, { length: b = 0, midpoint: x = { x: 0, y: 0 } } = y ?? {};
        v = b, g = x;
      } else if (l.curveStyle === "straight") {
        const y = d ? Td(d) : void 0, { length: b = 0, midpoint: x = { x: 0, y: 0 } } = y ?? {};
        v = b, g = x;
      } else {
        const y = d ? Pd(d) : void 0, { length: b = 0, midpoint: x = { x: 0, y: 0 } } = y ?? {};
        v = b, g = x;
      }
      if (d && v > 0)
        u = g.x, p = g.y, a === c && (u += 12, p -= 4);
      else {
        const y = r.source.x ?? 0, b = r.source.y ?? 0, x = r.target.x ?? 0, S = r.target.y ?? 0;
        u = (y + x) / 2, p = (b + S) / 2;
      }
      if (u = isFinite(u) ? u : 0, p = isFinite(p) ? p : 0, l.rotateLabel) {
        const y = (r.target.x ?? 0) - (r.source.x ?? 0), b = (r.target.y ?? 0) - (r.source.y ?? 0), x = Math.atan2(b, y) * 180 / Math.PI, S = x > 90 || x < -90 ? x + 180 : x;
        return `translate(${u}, ${p}) rotate(${S})`;
      } else
        return `translate(${u}, ${p})`;
    });
  }
  linkPathRouter(t) {
    const { from: e, to: n } = t;
    if (e.x === void 0 || e.y === void 0 || n.x === void 0 || n.y === void 0)
      return null;
    if (e === n)
      return this.linkSelfLoop(t);
    const r = n.getConnectedNodes(), s = this.getEdgeStyle(t);
    return s.curveStyle === "straight" ? this.linkStraight(t) : s.curveStyle === "curved" ? this.linkArc(t) : r.filter((o) => o.id === e.id).length > 0 ? (t.updateStyle({ edge: { curveStyle: "curved" } }), this.linkArc(t)) : (t.updateStyle({ edge: { curveStyle: "straight" } }), this.linkStraight(t));
  }
  linkSelfLoop(t) {
    var k;
    const { from: e, to: n } = t, r = ((k = this.graphSvgRenderer.getGraphInteraction().getSelectedEdge()) == null ? void 0 : k.edge.id) === t.id;
    if (e.x === void 0 || e.y === void 0 || n.x === void 0 || n.y === void 0)
      return null;
    const s = 4 + (r ? 2 : 0), o = 4 + (r ? 2 : 0), a = e.x ?? 0, c = e.y ?? 0, l = e.getCircleRadius() ? e.getCircleRadius() : this.graphSvgRenderer.nodeDrawer.getNodeStyle(e).size, h = l + 16 * Math.log(l + 1), d = Math.max(10, 110 / Math.sqrt(l)), u = 45, p = (u + d) * Math.PI / 180, g = a + h * Math.cos(p), v = c - h * Math.sin(p), y = (u - d) * Math.PI / 180, b = a + h * Math.cos(y), x = c - h * Math.sin(y), S = a + (l + s) * Math.cos(p), C = c - (l + s) * Math.sin(p), N = a + (l + o) * Math.cos(y), P = c - (l + o) * Math.sin(y);
    return `M ${S} ${C} C ${g} ${v}, ${b} ${x}, ${N} ${P}`;
  }
  linkStraight(t) {
    var N;
    const { from: e, to: n } = t, r = ((N = this.graphSvgRenderer.getGraphInteraction().getSelectedEdge()) == null ? void 0 : N.edge.id) === t.id;
    if (e.x === void 0 || e.y === void 0 || n.x === void 0 || n.y === void 0)
      return null;
    const s = this.graphSvgRenderer.edgeDrawer.getEdgeStyle(t), o = 4 + (s.markerStart !== void 0, 0) + 0, a = 4 + (s.markerEnd !== void 0 ? 2 : 0) + 2;
    let c = n.x - e.x, l = n.y - e.y, h = Math.sqrt(c * c + l * l), d = c / h, u = l / h;
    const p = e.getCircleRadius() ? e.getCircleRadius() : this.graphSvgRenderer.nodeDrawer.getNodeStyle(e).size, g = t.getSubgraphToNode() ?? t.to, v = g.getCircleRadius() ? g.getCircleRadius() : this.graphSvgRenderer.nodeDrawer.getNodeStyle(g).size;
    h === 0 && (d = -Math.SQRT1_2, u = -Math.SQRT1_2, c = d * p, l = u * p, h = p);
    const y = h <= p;
    let b, x, S, C;
    return y ? (b = e.x + p * d, x = e.y + p * u, S = n.x + (v + a) * d, C = n.y + (v + a) * u) : (b = e.x + (p + o) * d, x = e.y + (p + o) * u, S = n.x - (v + a) * d, C = n.y - (v + a) * u), `M ${b},${x} L ${S},${C}`;
  }
  linkArc(t) {
    var y;
    const { from: e, to: n } = t, r = ((y = this.graphSvgRenderer.getGraphInteraction().getSelectedEdge()) == null ? void 0 : y.edge.id) === t.id;
    if (e.x === void 0 || e.y === void 0 || n.x === void 0 || n.y === void 0)
      return null;
    const s = Math.hypot(n.x - e.x, n.y - e.y), o = this.graphSvgRenderer.edgeDrawer.getEdgeStyle(t), a = 4 + (o.markerStart !== void 0, 0) + (r ? 2 : 0), c = 4 + (o.markerStart !== void 0 ? 2 : 0) + (r ? 2 : 0), l = t.source.getCircleRadius() ? t.source.getCircleRadius() : this.graphSvgRenderer.nodeDrawer.getNodeStyle(e).size, h = t.target.getCircleRadius() ? t.target.getCircleRadius() : this.graphSvgRenderer.nodeDrawer.getNodeStyle(n).size, d = {
      from: { x: e.x, y: e.y },
      to: { x: n.x, y: n.y },
      rx: s,
      ry: s,
      xAxisRotation: 0
    }, u = {
      cx: e.x,
      cy: e.y,
      r: l + a
    }, p = {
      cx: n.x,
      cy: n.y,
      r: h + c
    }, g = _r(d, u), v = _r(d, p);
    return g && v ? `M${g.x},${g.y} A${s},${s} 0 0,1 ${v.x},${v.y}` : "";
  }
  defaultLabelRender(t, e, n) {
    var c;
    const r = t.append("g").classed("label-container", !0), s = Ls(e);
    if (!s || s === "") return;
    const a = (c = r.append("text").text(s).attr("text-anchor", "middle").attr("alignment-baseline", "middle").style("font-size", n.fontSize).style("font-family", n.fontFamily).style("pointer-events", "none").style("fill", n.color).node()) == null ? void 0 : c.getBBox();
    a && r.insert("rect", "text").attr("x", a.x - 4).attr("y", a.y - 2).attr("width", a.width + 8).attr("height", a.height + 4).attr("fill", n.backgroundColor).attr("rx", 2).attr("ry", 2);
  }
  renderDefinitions() {
    this.renderMarkers();
  }
  renderMarkers() {
    if (this.rendererOptions.markerStyleMap)
      for (const t in this.rendererOptions.markerStyleMap)
        this.renderMarker(this.rendererOptions.markerStyleMap[t], t);
  }
  renderMarker(t, e) {
    var a, c, l, h, d, u, p, g, v;
    const n = this.graphSvgRenderer.defs;
    if (!n.select(`#${e}`).empty()) return;
    n.append("marker").attr("id", e).attr("viewBox", t.viewBox).attr("refX", t.refX).attr("refY", t.refY).attr("markerWidth", t.markerWidth).attr("markerHeight", t.markerHeight).attr("markerUnits", t.markerUnits || "userSpaceOnUse").attr("orient", t.orient ?? "auto").append("path").attr("d", t.pathD).attr("fill", t.fill ?? "context-stroke");
    const s = e + "_selected";
    if (!n.select(`#${s}`).empty()) return;
    n.append("marker").attr("id", s).attr("viewBox", ((a = t.selected) == null ? void 0 : a.viewBox) ?? t.viewBox).attr("refX", ((c = t.selected) == null ? void 0 : c.refX) ?? t.refX).attr("refY", ((l = t.selected) == null ? void 0 : l.refY) ?? t.refY).attr("markerWidth", ((h = t.selected) == null ? void 0 : h.markerWidth) ?? t.markerWidth).attr("markerHeight", ((d = t.selected) == null ? void 0 : d.markerHeight) ?? t.markerHeight).attr("markerUnits", (((u = t.selected) == null ? void 0 : u.markerUnits) ?? t.markerUnits) || "userSpaceOnUse").attr("orient", ((p = t.selected) == null ? void 0 : p.orient) ?? t.orient ?? "auto").append("path").attr("d", ((g = t.selected) == null ? void 0 : g.pathD) ?? t.pathD).attr("fill", ((v = t.selected) == null ? void 0 : v.fill) ?? t.fill ?? "context-stroke");
  }
  highlightSelection(t, e) {
    var n, r, s;
    if (t.classed("selected", !1), ((n = this.graphSvgRenderer.getGraphInteraction().getSelectedEdge()) == null ? void 0 : n.edge.id) === e.id) {
      t.classed("selected", !0);
      const o = t.selectAll("path"), a = (r = o.attr("marker-start")) == null ? void 0 : r.match(/#.*(?=\))/);
      a && o.attr("marker-start", `url(${a[0]}_selected)`);
      const c = (s = o.attr("marker-end")) == null ? void 0 : s.match(/#.*(?=\))/);
      c && o.attr("marker-end", `url(${c[0]}_selected)`);
    }
  }
}
class Hd {
  constructor(t) {
    f(this, "graph");
    f(this, "renderer");
    f(this, "graphInteraction");
    this.graph = t;
  }
  init(t, e) {
    this.renderer = t, this.graphInteraction = e, this.registerListeners();
  }
  update() {
    this.registerListeners();
  }
  registerListeners() {
    this.renderer.getOptions().dragEnabled && this.renderer.getNodeSelection().call(this.graph.simulation.createDragBehavior()), this.renderer.getOptions().interactionEnabled && (this.renderer.getNodeSelection().on("dblclick.node", (t, e) => {
      var r;
      t.stopPropagation();
      const n = t.currentTarget;
      (r = this.graphInteraction) == null || r.nodeDbclick(n, t, e);
    }).on("click.node", (t, e) => {
      var r;
      t.stopPropagation();
      const n = t.currentTarget;
      (r = this.graphInteraction) == null || r.nodeClick(n, t, e);
    }).on("contextmenu.node", (t, e) => {
      var r;
      t.preventDefault(), t.stopPropagation();
      const n = t.currentTarget;
      (r = this.graphInteraction) == null || r.nodeContextmenu(n, t, e);
    }).on("mouseenter.node", (t, e) => {
      var r;
      const n = t.currentTarget;
      (r = this.graphInteraction) == null || r.nodeHoverIn(n, t, e);
    }).on("mouseleave.node", (t, e) => {
      var r;
      const n = t.currentTarget;
      (r = this.graphInteraction) == null || r.nodeHoverOut(n, t, e);
    }).on("dragging.node", (t, e) => {
      var n;
      (n = this.graphInteraction) == null || n.dragging(t, e);
    }), this.renderer.getEdgeSelection().on("dblclick.edge", (t, e) => {
      var r;
      t.stopPropagation();
      const n = t.currentTarget;
      (r = this.graphInteraction) == null || r.edgeDbclick(n, t, e);
    }).on("click.edge", (t, e) => {
      var r;
      t.stopPropagation();
      const n = t.currentTarget;
      (r = this.graphInteraction) == null || r.edgeClick(n, t, e);
    }).on("contextmenu.edge", (t, e) => {
      var r;
      t.preventDefault(), t.stopPropagation();
      const n = t.currentTarget;
      (r = this.graphInteraction) == null || r.edgeContextmenu(n, t, e);
    }).on("mouseenter.edge", (t, e) => {
      var r;
      const n = t.currentTarget;
      (r = this.graphInteraction) == null || r.edgeHoverIn(n, t, e);
    }).on("mouseleave.edge", (t, e) => {
      var r;
      const n = t.currentTarget;
      (r = this.graphInteraction) == null || r.edgeHoverOut(n, t, e);
    }), this.renderer.getCanvasSelection().on("click.canvas", (t) => {
      var e;
      (e = this.graphInteraction) == null || e.canvasClick(t);
    }).on("contextmenu.canvas", (t) => {
      var e;
      t.preventDefault(), (e = this.graphInteraction) == null || e.canvasContextmenu(t);
    }).on("mousemove.canvas", (t) => {
      var e;
      (e = this.graphInteraction) == null || e.canvasMousemove(t);
    }));
  }
}
var qe = typeof globalThis < "u" ? globalThis : typeof window < "u" ? window : typeof global < "u" ? global : typeof self < "u" ? self : {};
function $d(i) {
  return i && i.__esModule && Object.prototype.hasOwnProperty.call(i, "default") ? i.default : i;
}
var ve = { exports: {} };
ve.exports;
var kr;
function Gd() {
  return kr || (kr = 1, (function(i, t) {
    var e = 200, n = "__lodash_hash_undefined__", r = 800, s = 16, o = 9007199254740991, a = "[object Arguments]", c = "[object Array]", l = "[object AsyncFunction]", h = "[object Boolean]", d = "[object Date]", u = "[object Error]", p = "[object Function]", g = "[object GeneratorFunction]", v = "[object Map]", y = "[object Number]", b = "[object Null]", x = "[object Object]", S = "[object Proxy]", C = "[object RegExp]", N = "[object Set]", P = "[object String]", k = "[object Undefined]", A = "[object WeakMap]", I = "[object ArrayBuffer]", z = "[object DataView]", F = "[object Float32Array]", Z = "[object Float64Array]", Q = "[object Int8Array]", E = "[object Int16Array]", L = "[object Int32Array]", _ = "[object Uint8Array]", O = "[object Uint8ClampedArray]", B = "[object Uint16Array]", R = "[object Uint32Array]", H = /[\\^$.*+?()[\]{}|]/g, V = /^\[object .+?Constructor\]$/, j = /^(?:0|[1-9]\d*)$/, $ = {};
    $[F] = $[Z] = $[Q] = $[E] = $[L] = $[_] = $[O] = $[B] = $[R] = !0, $[a] = $[c] = $[I] = $[h] = $[z] = $[d] = $[u] = $[p] = $[v] = $[y] = $[x] = $[C] = $[N] = $[P] = $[A] = !1;
    var et = typeof qe == "object" && qe && qe.Object === Object && qe, mt = typeof self == "object" && self && self.Object === Object && self, lt = et || mt || Function("return this")(), pt = t && !t.nodeType && t, ct = pt && !0 && i && !i.nodeType && i, Zt = ct && ct.exports === pt, Ei = Zt && et.process, Fn = (function() {
      try {
        var m = ct && ct.require && ct.require("util").types;
        return m || Ei && Ei.binding && Ei.binding("util");
      } catch {
      }
    })(), zn = Fn && Fn.isTypedArray;
    function Zs(m, w, M) {
      switch (M.length) {
        case 0:
          return m.call(w);
        case 1:
          return m.call(w, M[0]);
        case 2:
          return m.call(w, M[0], M[1]);
        case 3:
          return m.call(w, M[0], M[1], M[2]);
      }
      return m.apply(w, M);
    }
    function Qs(m, w) {
      for (var M = -1, D = Array(m); ++M < m; )
        D[M] = w(M);
      return D;
    }
    function Js(m) {
      return function(w) {
        return m(w);
      };
    }
    function to(m, w) {
      return m == null ? void 0 : m[w];
    }
    function eo(m, w) {
      return function(M) {
        return m(w(M));
      };
    }
    var io = Array.prototype, no = Function.prototype, Ie = Object.prototype, Si = lt["__core-js_shared__"], Le = no.toString, zt = Ie.hasOwnProperty, Bn = (function() {
      var m = /[^.]+$/.exec(Si && Si.keys && Si.keys.IE_PROTO || "");
      return m ? "Symbol(src)_1." + m : "";
    })(), Rn = Ie.toString, ro = Le.call(Object), so = RegExp(
      "^" + Le.call(zt).replace(H, "\\$&").replace(/hasOwnProperty|(function).*?(?=\\\()| for .+?(?=\\\])/g, "$1.*?") + "$"
    ), Oe = Zt ? lt.Buffer : void 0, Hn = lt.Symbol, $n = lt.Uint8Array;
    Oe && Oe.allocUnsafe;
    var Gn = eo(Object.getPrototypeOf, Object), qn = Object.create, oo = Ie.propertyIsEnumerable, ao = io.splice, $t = Hn ? Hn.toStringTag : void 0, Te = (function() {
      try {
        var m = Ni(Object, "defineProperty");
        return m({}, "", {}), m;
      } catch {
      }
    })(), lo = Oe ? Oe.isBuffer : void 0, Vn = Math.max, co = Date.now, Un = Ni(lt, "Map"), he = Ni(Object, "create"), ho = /* @__PURE__ */ (function() {
      function m() {
      }
      return function(w) {
        if (!qt(w))
          return {};
        if (qn)
          return qn(w);
        m.prototype = w;
        var M = new m();
        return m.prototype = void 0, M;
      };
    })();
    function Gt(m) {
      var w = -1, M = m == null ? 0 : m.length;
      for (this.clear(); ++w < M; ) {
        var D = m[w];
        this.set(D[0], D[1]);
      }
    }
    function uo() {
      this.__data__ = he ? he(null) : {}, this.size = 0;
    }
    function po(m) {
      var w = this.has(m) && delete this.__data__[m];
      return this.size -= w ? 1 : 0, w;
    }
    function fo(m) {
      var w = this.__data__;
      if (he) {
        var M = w[m];
        return M === n ? void 0 : M;
      }
      return zt.call(w, m) ? w[m] : void 0;
    }
    function go(m) {
      var w = this.__data__;
      return he ? w[m] !== void 0 : zt.call(w, m);
    }
    function mo(m, w) {
      var M = this.__data__;
      return this.size += this.has(m) ? 0 : 1, M[m] = he && w === void 0 ? n : w, this;
    }
    Gt.prototype.clear = uo, Gt.prototype.delete = po, Gt.prototype.get = fo, Gt.prototype.has = go, Gt.prototype.set = mo;
    function Ot(m) {
      var w = -1, M = m == null ? 0 : m.length;
      for (this.clear(); ++w < M; ) {
        var D = m[w];
        this.set(D[0], D[1]);
      }
    }
    function vo() {
      this.__data__ = [], this.size = 0;
    }
    function yo(m) {
      var w = this.__data__, M = Pe(w, m);
      if (M < 0)
        return !1;
      var D = w.length - 1;
      return M == D ? w.pop() : ao.call(w, M, 1), --this.size, !0;
    }
    function bo(m) {
      var w = this.__data__, M = Pe(w, m);
      return M < 0 ? void 0 : w[M][1];
    }
    function wo(m) {
      return Pe(this.__data__, m) > -1;
    }
    function xo(m, w) {
      var M = this.__data__, D = Pe(M, m);
      return D < 0 ? (++this.size, M.push([m, w])) : M[D][1] = w, this;
    }
    Ot.prototype.clear = vo, Ot.prototype.delete = yo, Ot.prototype.get = bo, Ot.prototype.has = wo, Ot.prototype.set = xo;
    function Qt(m) {
      var w = -1, M = m == null ? 0 : m.length;
      for (this.clear(); ++w < M; ) {
        var D = m[w];
        this.set(D[0], D[1]);
      }
    }
    function Co() {
      this.size = 0, this.__data__ = {
        hash: new Gt(),
        map: new (Un || Ot)(),
        string: new Gt()
      };
    }
    function Mo(m) {
      var w = Fe(this, m).delete(m);
      return this.size -= w ? 1 : 0, w;
    }
    function Eo(m) {
      return Fe(this, m).get(m);
    }
    function So(m) {
      return Fe(this, m).has(m);
    }
    function _o(m, w) {
      var M = Fe(this, m), D = M.size;
      return M.set(m, w), this.size += M.size == D ? 0 : 1, this;
    }
    Qt.prototype.clear = Co, Qt.prototype.delete = Mo, Qt.prototype.get = Eo, Qt.prototype.has = So, Qt.prototype.set = _o;
    function Jt(m) {
      var w = this.__data__ = new Ot(m);
      this.size = w.size;
    }
    function ko() {
      this.__data__ = new Ot(), this.size = 0;
    }
    function No(m) {
      var w = this.__data__, M = w.delete(m);
      return this.size = w.size, M;
    }
    function Ao(m) {
      return this.__data__.get(m);
    }
    function Io(m) {
      return this.__data__.has(m);
    }
    function Lo(m, w) {
      var M = this.__data__;
      if (M instanceof Ot) {
        var D = M.__data__;
        if (!Un || D.length < e - 1)
          return D.push([m, w]), this.size = ++M.size, this;
        M = this.__data__ = new Qt(D);
      }
      return M.set(m, w), this.size = M.size, this;
    }
    Jt.prototype.clear = ko, Jt.prototype.delete = No, Jt.prototype.get = Ao, Jt.prototype.has = Io, Jt.prototype.set = Lo;
    function Oo(m, w) {
      var M = Li(m), D = !M && Ii(m), G = !M && !D && Kn(m), U = !M && !D && !G && Qn(m), X = M || D || G || U, q = X ? Qs(m.length, String) : [], W = q.length;
      for (var xt in m)
        X && // Safari 9 has enumerable `arguments.length` in strict mode.
        (xt == "length" || // Node.js 0.10 has enumerable non-index properties on buffers.
        G && (xt == "offset" || xt == "parent") || // PhantomJS 2 has enumerable non-index properties on typed arrays.
        U && (xt == "buffer" || xt == "byteLength" || xt == "byteOffset") || // Skip index properties.
        Xn(xt, W)) || q.push(xt);
      return q;
    }
    function _i(m, w, M) {
      (M !== void 0 && !ze(m[w], M) || M === void 0 && !(w in m)) && ki(m, w, M);
    }
    function To(m, w, M) {
      var D = m[w];
      (!(zt.call(m, w) && ze(D, M)) || M === void 0 && !(w in m)) && ki(m, w, M);
    }
    function Pe(m, w) {
      for (var M = m.length; M--; )
        if (ze(m[M][0], w))
          return M;
      return -1;
    }
    function ki(m, w, M) {
      w == "__proto__" && Te ? Te(m, w, {
        configurable: !0,
        enumerable: !0,
        value: M,
        writable: !0
      }) : m[w] = M;
    }
    var Po = Yo();
    function De(m) {
      return m == null ? m === void 0 ? k : b : $t && $t in Object(m) ? Xo(m) : ta(m);
    }
    function jn(m) {
      return de(m) && De(m) == a;
    }
    function Do(m) {
      if (!qt(m) || Qo(m))
        return !1;
      var w = Ti(m) ? so : V;
      return w.test(ra(m));
    }
    function Fo(m) {
      return de(m) && Zn(m.length) && !!$[De(m)];
    }
    function zo(m) {
      if (!qt(m))
        return Jo(m);
      var w = Wn(m), M = [];
      for (var D in m)
        D == "constructor" && (w || !zt.call(m, D)) || M.push(D);
      return M;
    }
    function Yn(m, w, M, D, G) {
      m !== w && Po(w, function(U, X) {
        if (G || (G = new Jt()), qt(U))
          Bo(m, w, X, M, Yn, D, G);
        else {
          var q = D ? D(Ai(m, X), U, X + "", m, w, G) : void 0;
          q === void 0 && (q = U), _i(m, X, q);
        }
      }, Jn);
    }
    function Bo(m, w, M, D, G, U, X) {
      var q = Ai(m, M), W = Ai(w, M), xt = X.get(W);
      if (xt) {
        _i(m, M, xt);
        return;
      }
      var vt = U ? U(q, W, M + "", m, w, X) : void 0, ue = vt === void 0;
      if (ue) {
        var Pi = Li(W), Di = !Pi && Kn(W), er = !Pi && !Di && Qn(W);
        vt = W, Pi || Di || er ? Li(q) ? vt = q : sa(q) ? vt = Vo(q) : Di ? (ue = !1, vt = $o(W)) : er ? (ue = !1, vt = qo(W)) : vt = [] : oa(W) || Ii(W) ? (vt = q, Ii(q) ? vt = aa(q) : (!qt(q) || Ti(q)) && (vt = Wo(W))) : ue = !1;
      }
      ue && (X.set(W, vt), G(vt, W, D, U, X), X.delete(W)), _i(m, M, vt);
    }
    function Ro(m, w) {
      return ia(ea(m, w, tr), m + "");
    }
    var Ho = Te ? function(m, w) {
      return Te(m, "toString", {
        configurable: !0,
        enumerable: !1,
        value: ca(w),
        writable: !0
      });
    } : tr;
    function $o(m, w) {
      return m.slice();
    }
    function Go(m) {
      var w = new m.constructor(m.byteLength);
      return new $n(w).set(new $n(m)), w;
    }
    function qo(m, w) {
      var M = Go(m.buffer);
      return new m.constructor(M, m.byteOffset, m.length);
    }
    function Vo(m, w) {
      var M = -1, D = m.length;
      for (w || (w = Array(D)); ++M < D; )
        w[M] = m[M];
      return w;
    }
    function Uo(m, w, M, D) {
      var G = !M;
      M || (M = {});
      for (var U = -1, X = w.length; ++U < X; ) {
        var q = w[U], W = void 0;
        W === void 0 && (W = m[q]), G ? ki(M, q, W) : To(M, q, W);
      }
      return M;
    }
    function jo(m) {
      return Ro(function(w, M) {
        var D = -1, G = M.length, U = G > 1 ? M[G - 1] : void 0, X = G > 2 ? M[2] : void 0;
        for (U = m.length > 3 && typeof U == "function" ? (G--, U) : void 0, X && Ko(M[0], M[1], X) && (U = G < 3 ? void 0 : U, G = 1), w = Object(w); ++D < G; ) {
          var q = M[D];
          q && m(w, q, D, U);
        }
        return w;
      });
    }
    function Yo(m) {
      return function(w, M, D) {
        for (var G = -1, U = Object(w), X = D(w), q = X.length; q--; ) {
          var W = X[++G];
          if (M(U[W], W, U) === !1)
            break;
        }
        return w;
      };
    }
    function Fe(m, w) {
      var M = m.__data__;
      return Zo(w) ? M[typeof w == "string" ? "string" : "hash"] : M.map;
    }
    function Ni(m, w) {
      var M = to(m, w);
      return Do(M) ? M : void 0;
    }
    function Xo(m) {
      var w = zt.call(m, $t), M = m[$t];
      try {
        m[$t] = void 0;
        var D = !0;
      } catch {
      }
      var G = Rn.call(m);
      return D && (w ? m[$t] = M : delete m[$t]), G;
    }
    function Wo(m) {
      return typeof m.constructor == "function" && !Wn(m) ? ho(Gn(m)) : {};
    }
    function Xn(m, w) {
      var M = typeof m;
      return w = w ?? o, !!w && (M == "number" || M != "symbol" && j.test(m)) && m > -1 && m % 1 == 0 && m < w;
    }
    function Ko(m, w, M) {
      if (!qt(M))
        return !1;
      var D = typeof w;
      return (D == "number" ? Oi(M) && Xn(w, M.length) : D == "string" && w in M) ? ze(M[w], m) : !1;
    }
    function Zo(m) {
      var w = typeof m;
      return w == "string" || w == "number" || w == "symbol" || w == "boolean" ? m !== "__proto__" : m === null;
    }
    function Qo(m) {
      return !!Bn && Bn in m;
    }
    function Wn(m) {
      var w = m && m.constructor, M = typeof w == "function" && w.prototype || Ie;
      return m === M;
    }
    function Jo(m) {
      var w = [];
      if (m != null)
        for (var M in Object(m))
          w.push(M);
      return w;
    }
    function ta(m) {
      return Rn.call(m);
    }
    function ea(m, w, M) {
      return w = Vn(w === void 0 ? m.length - 1 : w, 0), function() {
        for (var D = arguments, G = -1, U = Vn(D.length - w, 0), X = Array(U); ++G < U; )
          X[G] = D[w + G];
        G = -1;
        for (var q = Array(w + 1); ++G < w; )
          q[G] = D[G];
        return q[w] = M(X), Zs(m, this, q);
      };
    }
    function Ai(m, w) {
      if (!(w === "constructor" && typeof m[w] == "function") && w != "__proto__")
        return m[w];
    }
    var ia = na(Ho);
    function na(m) {
      var w = 0, M = 0;
      return function() {
        var D = co(), G = s - (D - M);
        if (M = D, G > 0) {
          if (++w >= r)
            return arguments[0];
        } else
          w = 0;
        return m.apply(void 0, arguments);
      };
    }
    function ra(m) {
      if (m != null) {
        try {
          return Le.call(m);
        } catch {
        }
        try {
          return m + "";
        } catch {
        }
      }
      return "";
    }
    function ze(m, w) {
      return m === w || m !== m && w !== w;
    }
    var Ii = jn(/* @__PURE__ */ (function() {
      return arguments;
    })()) ? jn : function(m) {
      return de(m) && zt.call(m, "callee") && !oo.call(m, "callee");
    }, Li = Array.isArray;
    function Oi(m) {
      return m != null && Zn(m.length) && !Ti(m);
    }
    function sa(m) {
      return de(m) && Oi(m);
    }
    var Kn = lo || ha;
    function Ti(m) {
      if (!qt(m))
        return !1;
      var w = De(m);
      return w == p || w == g || w == l || w == S;
    }
    function Zn(m) {
      return typeof m == "number" && m > -1 && m % 1 == 0 && m <= o;
    }
    function qt(m) {
      var w = typeof m;
      return m != null && (w == "object" || w == "function");
    }
    function de(m) {
      return m != null && typeof m == "object";
    }
    function oa(m) {
      if (!de(m) || De(m) != x)
        return !1;
      var w = Gn(m);
      if (w === null)
        return !0;
      var M = zt.call(w, "constructor") && w.constructor;
      return typeof M == "function" && M instanceof M && Le.call(M) == ro;
    }
    var Qn = zn ? Js(zn) : Fo;
    function aa(m) {
      return Uo(m, Jn(m));
    }
    function Jn(m) {
      return Oi(m) ? Oo(m) : zo(m);
    }
    var la = jo(function(m, w, M) {
      Yn(m, w, M);
    });
    function ca(m) {
      return function() {
        return m;
      };
    }
    function tr(m) {
      return m;
    }
    function ha() {
      return !1;
    }
    i.exports = la;
  })(ve, ve.exports)), ve.exports;
}
var qd = Gd();
const re = /* @__PURE__ */ $d(qd);
class Vd {
  constructor(t) {
    f(this, "graph");
    f(this, "callbacks");
    f(this, "listeners");
    f(this, "selectedNode", null);
    f(this, "selectedEdge", null);
    f(this, "selectedNodes", []);
    f(this, "selectedEdges", []);
    f(this, "nodeHoverIn", (t, e, n) => {
      this.emit("nodeHoverIn", e, n, t), this.callbacks.onNodeHoverIn && typeof this.callbacks.onNodeHoverIn == "function" && this.callbacks.onNodeHoverIn(e, n, t);
    });
    f(this, "nodeHoverOut", (t, e, n) => {
      this.emit("nodeHoverOut", e, n, t), this.callbacks.onNodeHoverOut && typeof this.callbacks.onNodeHoverOut == "function" && this.callbacks.onNodeHoverOut(e, n, t);
    });
    f(this, "dragging", (t, e) => {
      this.emit("dragging", t, e), this.callbacks.onNodeDragging && typeof this.callbacks.onNodeDragging == "function" && this.callbacks.onNodeDragging(t, e);
    });
    f(this, "dragended", (t, e) => {
      this.emit("dragended", t, e), this.callbacks.onNodeDragended && typeof this.callbacks.onNodeDragended == "function" && this.callbacks.onNodeDragended(t, e);
    });
    this.graph = t, this.callbacks = this.graph.getCallbacks() ?? {}, this.listeners = {
      nodeClick: [],
      nodeDbclick: [],
      nodeHoverIn: [],
      nodeHoverOut: [],
      nodeSelect: [],
      nodeBlur: [],
      dragging: [],
      dragended: [],
      nodeContextmenu: [],
      edgeClick: [],
      edgeDbclick: [],
      edgeHoverIn: [],
      edgeHoverOut: [],
      edgeSelect: [],
      edgeBlur: [],
      edgeContextmenu: [],
      canvasClick: [],
      canvasMousemove: [],
      canvasContextmenu: [],
      canvasZoom: [],
      simulationTick: [],
      simulationSlowTick: [],
      selectNode: [],
      unselectNode: [],
      selectEdge: [],
      unselectEdge: [],
      selectNodes: [],
      unselectNodes: [],
      selectEdges: [],
      unselectEdges: []
    }, this.graph.UIManager.keyManager.register({ key: "Enter", callback: () => {
      this.expandNodeSelection();
    } });
  }
  on(t, e) {
    this.listeners[t].push(e);
  }
  off(t, e) {
    this.listeners[t] = this.listeners[t].filter((n) => n !== e);
  }
  getGraph() {
    return this.graph;
  }
  emit(t, ...e) {
    for (const n of this.listeners[t])
      n(...e);
  }
  nodeClick(t, e, n) {
    var r;
    e.shiftKey ? this.addNodesToSelection([{ node: n, element: t }]) : ((r = this.getSelectedNode()) == null ? void 0 : r.node) !== n && (t.classList.contains("pvt-node-expanded"), this.selectNode(t, n)), this.emit("nodeClick", e, n, t), this.callbacks.onNodeClick && typeof this.callbacks.onNodeClick == "function" && this.callbacks.onNodeClick(e, n, t);
  }
  nodeDbclick(t, e, n) {
    this.emit("nodeDbclick", e, n, t), this.callbacks.onNodeDbclick && typeof this.callbacks.onNodeDbclick == "function" && this.callbacks.onNodeDbclick(e, n, t);
  }
  nodeContextmenu(t, e, n) {
    this.emit("nodeContextmenu", e, n, t), this.callbacks.onNodeContextmenu && typeof this.callbacks.onNodeContextmenu == "function" && this.callbacks.onNodeContextmenu(e, n, t);
  }
  edgeClick(t, e, n) {
    this.selectEdge(t, n), this.emit("edgeClick", e, n, t), this.callbacks.onEdgeClick && typeof this.callbacks.onEdgeClick == "function" && this.callbacks.onEdgeClick(e, n, t);
  }
  edgeDbclick(t, e, n) {
    this.emit("edgeDbclick", e, n, t), this.callbacks.onEdgeDbclick && typeof this.callbacks.onEdgeDbclick == "function" && this.callbacks.onEdgeDbclick(e, n, t);
  }
  edgeContextmenu(t, e, n) {
    this.emit("edgeContextmenu", e, n, t), this.callbacks.onEdgeContextmenu && typeof this.callbacks.onEdgeContextmenu == "function" && this.callbacks.onEdgeContextmenu(e, n, t);
  }
  edgeHoverIn(t, e, n) {
    this.emit("edgeHoverIn", e, n, t), this.callbacks.onEdgeHoverIn && typeof this.callbacks.onEdgeHoverIn == "function" && this.callbacks.onEdgeHoverIn(e, n, t);
  }
  edgeHoverOut(t, e, n) {
    this.emit("edgeHoverOut", e, n, t), this.callbacks.onEdgeHoverOut && typeof this.callbacks.onNodeHoverOut == "function" && this.callbacks.onEdgeHoverOut(e, n, t);
  }
  canvasClick(t) {
    this.unselectAll(), this.emit("canvasClick", t), this.callbacks.onCanvasClick && typeof this.callbacks.onCanvasClick == "function" && this.callbacks.onCanvasClick(t);
  }
  canvasZoom(t) {
    this.emit("canvasZoom", t), this.callbacks.onCanvasZoom && typeof this.callbacks.onCanvasZoom == "function" && this.callbacks.onCanvasZoom(t);
  }
  canvasContextmenu(t) {
    this.emit("canvasContextmenu", t), this.callbacks.onCanvasContextmenu && typeof this.callbacks.onCanvasContextmenu == "function" && this.callbacks.onCanvasContextmenu(t);
  }
  canvasMousemove(t) {
    this.emit("canvasMousemove", t), this.callbacks.onCanvasMousemove && typeof this.callbacks.onCanvasMousemove == "function" && this.callbacks.onCanvasMousemove(t);
  }
  simulationTick() {
    this.emit("simulationTick"), this.callbacks.onSimulationTick && typeof this.callbacks.onSimulationTick == "function" && this.callbacks.onSimulationTick();
  }
  simulationSlowTick() {
    this.emit("simulationSlowTick"), this.callbacks.onSimulationSlowTick && typeof this.callbacks.onSimulationSlowTick == "function" && this.callbacks.onSimulationSlowTick();
  }
  selectNode(t, e) {
    this.unselectAll(), this.selectedNode = {
      node: e,
      element: t
    }, this.selectedNodes = [this.selectedNode], this.emit("selectNode", e, t), this.callbacks.onNodeSelect && typeof this.callbacks.onNodeSelect == "function" && this.callbacks.onNodeSelect(e, t), this.refreshRendering();
  }
  unselectNode() {
    if (this.selectedNode === null)
      return;
    const t = this.selectedNode.node, e = this.selectedNode.element;
    this.selectedNode = null, this.selectedNodes = [], this.emit("unselectNode", t, e), this.callbacks.onNodeBlur && typeof this.callbacks.onNodeBlur == "function" && this.callbacks.onNodeBlur(t, e), this.unselectFromDirectSubgraph(t), this.refreshRendering();
  }
  unselectFromAncestorSubgraphs(t) {
    var a, c;
    const e = this.buildAncestorStack(t);
    let n = this.findOutermostSubgraph(e);
    if (!n) return;
    let r;
    for (; e.length > 0 && n; ) {
      const l = e.pop();
      r = n, l && (n = (a = n.getMutableNode(l.id)) == null ? void 0 : a.getSubgraph());
    }
    if (!r) return;
    const s = r.renderer.getGraphInteraction();
    ((c = s.getSelectedNode()) == null ? void 0 : c.node.id) === t.id && s.unselectNode();
  }
  unselectFromDirectSubgraph(t) {
    var n, r;
    const e = (n = t.parentNode) == null ? void 0 : n.getSubgraph();
    if (e) {
      const s = e.renderer.getGraphInteraction();
      ((r = s.getSelectedNode()) == null ? void 0 : r.node.id) === t.id && s.unselectNode();
    }
    this.refreshRendering();
  }
  buildAncestorStack(t) {
    const e = [];
    let n = t.parentNode;
    for (; n; )
      e.push(n), n = n.parentNode;
    return e;
  }
  findOutermostSubgraph(t) {
    var e;
    for (let n = t.length - 1; n >= 0; n--) {
      const r = (e = t[n]) == null ? void 0 : e.getSubgraph();
      if (r) return r;
    }
  }
  selectNodes(t) {
    if (t.length === 1)
      return this.selectNode(t[0].element, t[0].node);
    this.unselectAll(), this.selectedNodes = t, this.emit("selectNodes", this.selectedNodes), this.callbacks.onNodesSelect && typeof this.callbacks.onNodesSelect == "function" && this.callbacks.onNodesSelect(t), this.refreshRendering();
  }
  addNodesToSelection(t) {
    if (t.length == 0) return;
    if (this.selectedNodes.length === 0 && t.length === 1)
      return this.selectNode(t[0].element, t[0].node);
    const e = this.getSelectedNodeIDs() ?? [];
    t = t.filter((n) => !e.includes(n.node.id)), this.selectedNodes = this.selectedNodes.concat(t), this.callbacks.onNodesSelect && typeof this.callbacks.onNodesSelect == "function" && this.callbacks.onNodesSelect(t), this.emit("selectNodes", t), this.refreshRendering();
  }
  removeNodesFromSelection(t) {
    const e = t.map((n) => n.node.id);
    this.selectedNodes = this.selectedNodes.filter((n) => !e.includes(n.node.id)), t.forEach(({ node: n, element: r }) => {
      this.callbacks.onNodeBlur && typeof this.callbacks.onNodeBlur == "function" && this.callbacks.onNodeBlur(n, r);
    }), this.emit("unselectNodes", t), this.refreshRendering();
  }
  selectEdge(t, e) {
    this.unselectAll(), this.selectedEdge = {
      edge: e,
      element: t
    }, this.emit("selectEdge", e, t), this.callbacks.onEdgeSelect && typeof this.callbacks.onEdgeSelect == "function" && this.callbacks.onEdgeSelect(e, t), this.refreshRendering();
  }
  selectEdges(t) {
    this.unselectAll(), this.selectedEdges = t.map((e) => ({
      edge: e[0],
      element: e[1]
    })), this.emit("selectEdges", this.selectedEdges), this.selectedEdges.forEach(({ edge: e, element: n }) => {
      this.callbacks.onEdgeSelect && typeof this.callbacks.onEdgeSelect == "function" && this.callbacks.onEdgeSelect(e, n);
    }), this.refreshRendering();
  }
  unselectEdge() {
    if (this.selectedEdge === null)
      return;
    const t = this.selectedEdge.edge, e = this.selectedEdge.element;
    this.selectedEdge = null, this.emit("unselectEdge", t, e), this.callbacks.onEdgeBlur && typeof this.callbacks.onEdgeBlur == "function" && this.callbacks.onEdgeBlur(t, e), this.refreshRendering();
  }
  unselectAll() {
    this.unselectNode(), this.unselectEdge(), this.clearNodeSelectionList(), this.clearEdgeSelectionList(), this.refreshRendering();
  }
  clearNodeSelectionList() {
    this.selectedNodes.forEach(({ node: t, element: e }) => {
      this.callbacks.onNodeBlur && typeof this.callbacks.onNodeBlur == "function" && this.callbacks.onNodeBlur(t, e);
    }), this.selectedNodes = [], this.emit("unselectNodes", this.selectedNodes);
  }
  clearEdgeSelectionList() {
    this.emit("unselectEdges", this.selectedEdges), this.selectedEdges.forEach(({ edge: t, element: e }) => {
      this.callbacks.onEdgeBlur && typeof this.callbacks.onEdgeBlur == "function" && this.callbacks.onEdgeBlur(t, e);
    }), this.selectedEdges = [];
  }
  hasActiveMultiselection() {
    return this.selectedNodes.length > 1 || this.selectedEdges.length > 1;
  }
  refreshRendering() {
    this.graph.renderer.update(!1), this.graph.renderer.nextTick();
  }
  getSelectedNode() {
    return this.selectedNode;
  }
  getSelectedEdge() {
    return this.selectedEdge;
  }
  getSelectedNodeIDs() {
    var t;
    return ((t = this.selectedNodes) == null ? void 0 : t.map((e) => e.node.id)) ?? null;
  }
  getSelectedNodes() {
    return this.selectedNodes;
  }
  getSelectedEdgeIDs() {
    var t;
    return ((t = this.selectedEdges) == null ? void 0 : t.map((e) => e.edge.id)) ?? null;
  }
  getSelectedEdges() {
    return this.selectedEdges;
  }
  expandNodeSelection() {
    this.selectedNodes.length > 1 ? this.graph.toggleExpandNodes(this.selectedNodes.map((t) => t.node)) : this.selectedNode && this.graph.toggleExpandNode(this.selectedNode.node);
  }
}
class Ud {
  constructor(t, e, n) {
    f(this, "graph");
    f(this, "container");
    f(this, "options");
    f(this, "layoutProgress", 0);
    f(this, "layoutProgressType", "done");
    f(this, "progressBar", null);
    f(this, "timerLabel", null);
    f(this, "textLabel", null);
    f(this, "loadingPb", null);
    this.graph = t, this.container = e, this.options = n;
  }
  getCanvas() {
    return this.container.querySelector(".pvt-canvas");
  }
  updateLayoutProgress(t, e, n) {
    this.layoutProgress = t, this.layoutProgressType = n, !(!this.progressBar || !this.timerLabel || !this.textLabel) && (this.progressBar.style.width = `${t * 100}%`, this.timerLabel.textContent = `Elapsed time: ${(e / 1e3).toFixed(1)} sec`, this.layoutProgressType === "simulation" ? this.textLabel.textContent = "Optimizing node positions..." : this.layoutProgressType === "rendering" ? (this.progressBar.style.width = "100%", this.textLabel.textContent = "Rendering in progress") : this.layoutProgressType === "done" && (this.progressBar.style.width = "100%", this.timerLabel.textContent = "All done"), this.toggleLayoutProgressVisibility());
  }
  toggleLayoutProgressVisibility() {
    const t = this.getZoomGroup();
    t && t.classList.toggle("hidden", this.layoutProgressType !== "done"), this.loadingPb && this.loadingPb.classList.toggle("hidden", this.layoutProgressType === "done");
  }
  setupRendering() {
    this.createHtmlProgressBar();
  }
  createHtmlProgressBar() {
    const t = this.getCanvas();
    if (!t)
      throw new Error("Canvas element is not defined in the graph renderer.");
    const e = document.createElement("div");
    e.classList.add("pvt-loading-progress-bar"), e.style.position = "absolute", e.style.left = "50%", e.style.top = "50%", e.style.transform = "translate(-50%, -50%)";
    const n = document.createElement("div");
    n.classList.add("background"), n.style.width = "100%";
    const r = document.createElement("div");
    r.classList.add("track"), n.style.width = "100%";
    const s = document.createElement("div");
    s.classList.add("fill"), s.style.width = "0px";
    const o = document.createElement("span");
    o.classList.add("label"), o.textContent = "Optimizing node positions...";
    const a = document.createElement("span");
    a.classList.add("label"), a.textContent = "Elapsed time: 0 sec", r.appendChild(s), n.appendChild(r), e.append(n, o, a), t.appendChild(e), this.progressBar = s, this.timerLabel = a, this.textLabel = o, this.loadingPb = e;
  }
}
class jd {
}
class Yd extends jd {
  constructor(e, n, r) {
    super();
    f(this, "renderer");
    f(this, "svg");
    f(this, "selectionBoxGroup");
    f(this, "rect", null);
    f(this, "startX", 0);
    f(this, "startY", 0);
    f(this, "isSelecting", !1);
    f(this, "selectionMode", "start");
    f(this, "onSvgMouseLeave", () => {
      this.isSelecting && this.onMouseUp();
    });
    f(this, "onMouseDown", (e) => {
      if (!this.selectionBoxGroup) return;
      if (e.shiftKey)
        this.selectionMode = "add";
      else if (e.altKey)
        this.selectionMode = "start";
      else if (e.ctrlKey)
        this.selectionMode = "remove";
      else {
        this.selectionMode = "start";
        return;
      }
      e.preventDefault(), this.svg.querySelectorAll(".pvt-selection-rectangle").forEach((s) => s.remove()), this.isSelecting = !0;
      const { x: n, y: r } = this.getSvgPoint(e);
      this.startX = n, this.startY = r, this.rect = document.createElementNS("http://www.w3.org/2000/svg", "rect"), this.rect.setAttribute("x", n.toString()), this.rect.setAttribute("y", r.toString()), this.rect.setAttribute("width", "0"), this.rect.setAttribute("height", "0"), this.rect.setAttribute("class", "pvt-selection-rectangle"), this.selectionBoxGroup.appendChild(this.rect), this.svg.addEventListener("mouseleave", this.onSvgMouseLeave);
    });
    f(this, "onMouseMove", (e) => {
      if (!this.isSelecting || !this.rect) return;
      const { x: n, y: r } = this.getSvgPoint(e), s = Math.min(this.startX, n), o = Math.min(this.startY, r), a = Math.abs(n - this.startX), c = Math.abs(r - this.startY);
      this.rect.setAttribute("x", s.toString()), this.rect.setAttribute("y", o.toString()), this.rect.setAttribute("width", a.toString()), this.rect.setAttribute("height", c.toString());
    });
    f(this, "onMouseUp", () => {
      if (!this.selectionBoxGroup || !this.isSelecting || !this.rect) return;
      this.isSelecting = !1;
      const e = this.rect.getBoundingClientRect(), n = this.getNodesInRect(e).map((r) => ({
        node: r[0],
        element: r[1]
      }));
      this.selectionMode == "start" ? this.renderer.getGraphInteraction().selectNodes(n) : this.selectionMode == "add" ? this.renderer.getGraphInteraction().addNodesToSelection(n) : this.selectionMode == "remove" && this.renderer.getGraphInteraction().removeNodesFromSelection(n), this.selectionBoxGroup.removeChild(this.rect), this.rect = null, this.svg.removeEventListener("mouseleave", this.onSvgMouseLeave);
    });
    this.renderer = e, this.svg = n, this.selectionBoxGroup = r, this.init();
  }
  selectionInProgress() {
    return this.isSelecting;
  }
  init() {
    this.svg.addEventListener("mousedown", this.onMouseDown), this.svg.addEventListener("mousemove", this.onMouseMove), this.svg.addEventListener("mouseup", this.onMouseUp);
  }
  getSvgPoint(e) {
    var r;
    const n = this.svg.createSVGPoint();
    return n.x = e.clientX, n.y = e.clientY, n.matrixTransform((r = this.svg.getScreenCTM()) == null ? void 0 : r.inverse());
  }
  getNodesInRect(e) {
    const n = this.renderer.getGraphInteraction().getGraph().getMutableNodes(), r = [];
    return n.forEach((s) => {
      if (!s.x || !s.y) return;
      const o = s.getGraphElement();
      if (!o || !(o instanceof SVGGElement)) return;
      const a = o.getBoundingClientRect();
      a.x < e.x + e.width && a.x + a.width > e.x && a.y < e.y + e.height && a.y + a.height > e.y && r.push([s, o]);
    }), r;
  }
}
tt.prototype.transition = In;
const Xd = {
  arrow: {
    pathD: "M0,-5L10,0L0,5",
    viewBox: "0 -5 10 10",
    refX: 6,
    refY: 0,
    markerWidth: 12,
    markerHeight: 12,
    markerUnits: "userSpaceOnUse",
    orient: "auto",
    selected: {
      fill: "var(--pvt-edge-selected-stroke, #007acc)"
    }
  },
  circle: {
    pathD: "M5,5m-3,0a3,3 0 1,0 6,0a3,3 0 1,0 -6,0",
    viewBox: "0 0 10 10",
    refX: 5,
    refY: 5,
    markerWidth: 10,
    markerHeight: 10,
    markerUnits: "userSpaceOnUse",
    orient: 0,
    selected: {
      fill: "var(--pvt-edge-selected-stroke, #007acc)",
      markerWidth: 16,
      markerHeight: 16
    }
  },
  diamond: {
    pathD: "M0,-4L4,0L0,4L-4,0Z",
    viewBox: "-5 -5 10 10",
    refX: 0,
    refY: 0,
    markerWidth: 8,
    markerHeight: 8,
    markerUnits: "userSpaceOnUse",
    orient: 0,
    selected: {
      fill: "var(--pvt-edge-selected-stroke, #007acc)",
      markerWidth: 14,
      markerHeight: 14
    }
  },
  bigcircle: {
    pathD: "M5,5m-3,0a3,3 0 1,0 6,0a3,3 0 1,0 -6,0",
    viewBox: "0 0 10 10",
    refX: 5,
    refY: 5,
    markerWidth: 16,
    markerHeight: 16,
    markerUnits: "userSpaceOnUse",
    orient: 0,
    selected: {
      fill: "var(--pvt-edge-selected-stroke, #007acc)",
      markerWidth: 24,
      markerHeight: 24
    }
  }
}, Wd = {
  shape: "circle",
  size: 10,
  strokeWidth: "var(--pvt-node-stroke-width, 2)",
  color: "var(--pvt-node-color, #007acc)",
  strokeColor: "var(--pvt-node-stroke, #fff)",
  fontFamily: "var(--pvt-label-font, system-ui, sans-serif)",
  textColor: "var(--pvt-node-text-color, #fff)",
  textVerticalShift: 0,
  iconUnicode: void 0,
  iconClass: void 0,
  svgIcon: void 0,
  imagePath: void 0,
  text: void 0,
  html: void 0
}, Kd = {
  strokeWidth: 2,
  opacity: 1,
  curveStyle: "bidirectional",
  dashed: !1,
  animateDash: !0,
  rotateLabel: !1,
  markerEnd: "arrow",
  markerStart: void 0,
  strokeColor: "var(--pvt-edge-stroke, #999)"
}, Zd = {
  fontSize: 12,
  fontFamily: "var(--pvt-label-font, system-ui, sans-serif)",
  color: "var(--pvt-edge-label-color, #333)",
  backgroundColor: "var(--pvt-edge-label-bg, #ffffffa0)"
}, Qd = {
  type: "svg",
  enableFocusMode: !0,
  enableNodeExpansion: !0,
  beforeRender: () => {
  },
  zoomEnabled: !0,
  dragEnabled: !0,
  interactionEnabled: !0,
  minZoom: 0.05,
  maxZoom: 10,
  zoomAnimation: !0,
  zoomAnimationDuration: 300,
  defaultNodeStyle: Wd,
  defaultEdgeStyle: Kd,
  defaultLabelStyle: Zd,
  markerStyleMap: Xd,
  selectionBox: {
    enabled: !0
  }
};
class Jd extends Ud {
  constructor(e, n, r, s) {
    super(e, n, s);
    f(this, "options");
    f(this, "zoom");
    f(this, "eventHandler");
    f(this, "selectionBox", null);
    f(this, "graphInteraction");
    f(this, "nodeDrawer");
    f(this, "edgeDrawer");
    f(this, "svgCanvas");
    // private progressBar: SVGRectElement
    f(this, "svg");
    f(this, "zoomGroup");
    f(this, "edgeGroup");
    f(this, "nodeGroup");
    f(this, "selectionBoxGroup");
    f(this, "defs");
    f(this, "nodeGroupSelection");
    f(this, "edgeGroupSelection");
    f(this, "nodeSelection");
    f(this, "edgeSelection");
    this.options = re({}, Qd, s), this.graphInteraction = r, this.eventHandler = new Hd(this.graph), this.nodeDrawer = new wi(this.options, this.graph, this), this.edgeDrawer = new Rd(this.options, this.graph, this), this.svgCanvas = document.createElementNS("http://www.w3.org/2000/svg", "svg"), this.svgCanvas.setAttribute("width", "100%"), this.svgCanvas.setAttribute("height", "100%"), this.svgCanvas.setAttribute("fill", "none"), this.svgCanvas.setAttribute("class", "pvt-canvas-element"), this.svgCanvas.setAttribute("data-renderer-drag-enabled", this.options.dragEnabled ? "1" : "0"), this.getCanvas().appendChild(this.svgCanvas), this.svg = tt(this.svgCanvas), this.zoomGroup = this.svg.append("g").attr("class", "zoom-layer hidden"), this.edgeGroup = this.zoomGroup.append("g").attr("class", "edges"), this.selectionBoxGroup = this.svg.append("g").attr("class", "selection-box"), this.nodeGroup = this.zoomGroup.append("g").attr("class", "nodes"), this.defs = this.svg.append("defs"), this.edgeDrawer.renderDefinitions(), this.zoom = Wh(), this.zoom = this.zoom.filter((a) => {
      if (!this.options.zoomEnabled || a.ctrlKey || a.shiftKey || a.altKey)
        return !1;
      const c = a.target;
      return !(c.tagName === "INPUT" || c.tagName === "SELECT" || c.tagName === "TEXTAREA");
    }).scaleExtent([this.options.minZoom, this.options.maxZoom]).on("zoom", (a) => {
      this.zoomGroup.attr("transform", a.transform), this.graphInteraction.canvasZoom(a);
    }), this.svg.call(this.zoom), this.svg.on("dblclick.zoom", null), this.options.selectionBox.enabled && (this.selectionBox = new Yd(this, this.svgCanvas, this.selectionBoxGroup.node())), new IntersectionObserver((a) => {
      a.forEach((c) => {
        c.isIntersecting && this.nodeSelection.each((l, h, d) => {
          if (l.getCircleRadius() !== 25) return;
          const u = d[h].getBBox();
          l.setCircleRadius(0.5 * Math.max(u.width, u.height));
        });
      });
    }, { threshold: 0 }).observe(this.svgCanvas);
  }
  setupRendering() {
    this.createHtmlProgressBar();
  }
  getZoomBehavior() {
    return this.zoom;
  }
  getSelectionBox() {
    return this.selectionBox;
  }
  getOptions() {
    return this.options;
  }
  init() {
    this.options.beforeRender && this.options.beforeRender(this.graph), this.dataUpdate(), this.eventHandler.init(this, this.graphInteraction);
  }
  update(e = !1) {
    this.dataUpdate(), e && this.eventHandler.update();
  }
  dataUpdate() {
    const e = this.graph.getMutableNodes().filter((s) => s.visible), n = this.nodeGroup.node();
    this.nodeGroupSelection = this.nodeGroup.selectAll("g.pvt-node").filter(function() {
      return this.parentNode === n;
    }), this.nodeSelection = this.nodeGroupSelection.data(e, (s) => s.id).join(
      (s) => s.append("g").classed("pvt-node", !0).classed("pvt-node-has-children", (o) => o.hasChildren()).classed("pvt-node-expanded", (o) => o.expanded === !0).each((o, a, c) => {
        o.clearDirty();
        const l = tt(c[a]);
        l.attr("id", `node-${o.domID}`), this.nodeDrawer.render(l, o);
      }),
      (s) => s.classed("pvt-node-expanded", (o) => o.expanded === !0).each((o, a, c) => {
        const l = tt(c[a]);
        if (o.isDirty()) {
          if (o.clearDirty(), !o.expanded) {
            it.collapseAllOpenedClusters(o), it.toggleSyntheticEdges(o);
            const h = this.nodeDrawer.graph.getParentGraph();
            let d = h;
            for (; d; )
              d.renderer.update(!1), d = d.getParentGraph();
            h && it.updateToNewRadiusCollapsed(o, !0, h);
          }
          l.selectChildren().remove(), this.nodeDrawer.render(l, o);
        }
        this.nodeDrawer.checkForHighlight(l, o);
      }),
      (s) => s.remove()
    );
    const r = this.graph.getMutableEdges().filter((s) => s.visible);
    this.edgeGroupSelection = this.edgeGroup.selectAll("g.pvt-edge-group"), this.edgeSelection = this.edgeGroupSelection.data(r, (s) => s.id).join(
      (s) => s.append("g").classed("pvt-edge-group", !0).classed("pvt-edge-synthetic", (o) => o.isSynthetic === !0).each((o, a, c) => {
        o.clearDirty();
        const l = tt(c[a]);
        l.attr("id", `edge-${o.domID}`), this.edgeDrawer.render(l, o);
      }),
      (s) => s.each((o, a, c) => {
        if (o.isDirty()) {
          o.clearDirty();
          const l = tt(c[a]);
          l.selectChildren().remove(), this.edgeDrawer.render(l, o);
        }
      }),
      (s) => s.remove()
    );
  }
  getCanvasSelection() {
    return this.svg;
  }
  getZoomGroup() {
    return this.zoomGroup.node();
  }
  nextTick() {
    this.updateEdgePositions(), this.updateNodePositions();
  }
  nextTickFor(e) {
    this.updateEdgePositions(e), this.updateNodePositions(e);
  }
  zoomIn() {
    const e = this.getZoomBehavior(), n = this.getCanvasSelection();
    !e || !n || (this.options.zoomAnimation ? n.transition().duration(300).call(e.scaleBy, 1.5) : n.call(e.scaleBy, 1.5));
  }
  zoomOut() {
    const e = this.getZoomBehavior(), n = this.getCanvasSelection();
    !e || !n || (this.options.zoomAnimation ? n.transition().duration(300).call(e.scaleBy, 0.667) : n.call(e.scaleBy, 0.667));
  }
  fitAndCenter(e) {
    const n = this.getZoomBehavior(), r = this.getCanvasSelection(), s = r.node(), o = r.select(".zoom-layer").node();
    if (!n || !s || !o) return;
    const a = o.getBBox();
    if (a.width == 0 || a.height == 0) return;
    const c = s.clientWidth, l = s.clientHeight, h = a.width, d = a.height, u = a.x + h / 2, p = a.y + d / 2;
    let g;
    e ? g = e : (g = Math.min(
      c / h,
      l / d
    ) * 0.8, g = Math.min(g, 3));
    const v = c / 2 - g * u, y = l / 2 - g * p, b = ui.translate(v, y).scale(g);
    this.options.zoomAnimation ? r.transition().duration(this.options.zoomAnimationDuration).call(n.transform, b) : r.call(n.transform, b);
  }
  focusElement(e) {
    const n = e.getGraphElement(), r = this.getZoomBehavior(), s = this.getCanvasSelection(), o = s.node(), a = s.select(".zoom-layer").node();
    if (!r || !o || !a || !n) return;
    const c = a.getBBox(), l = o.clientWidth, h = o.clientHeight, d = c.width, u = c.height, p = n.transform.baseVal;
    let g = 0, v = 0;
    if (p.numberOfItems > 0) {
      const C = p.getItem(0);
      g = C.matrix.e, v = C.matrix.f;
    }
    const y = Math.min(
      l / d,
      h / u
    ) * 1.5, b = l / 2 - y * g, x = h / 2 - y * v, S = ui.translate(b, x).scale(y);
    s.transition().duration(300).call(r.transform, S);
  }
  highlightElement(e) {
    const n = e.getGraphElement();
    e instanceof _t ? (this.edgeSelection.classed("pvt-edge-highlighted", !1), n == null || n.classList.add("pvt-edge-highlighted")) : e instanceof Mt && (this.nodeSelection.classed("pvt-node-highlighted", !1), n == null || n.classList.add("pvt-node-highlighted"));
  }
  unHighlightElement(e) {
    const n = e.getGraphElement();
    e instanceof _t ? n == null || n.classList.remove("pvt-edge-highlighted") : e instanceof Mt && (n == null || n.classList.remove("pvt-node-highlighted"));
  }
  clearHighlightedElements() {
    this.edgeSelection.classed("pvt-edge-highlighted", !1), this.nodeSelection.classed("pvt-node-highlighted", !1);
  }
  updateNodePositions(e) {
    if (e) {
      const n = new Set(e == null ? void 0 : e.map((s) => s.id)), r = this.nodeSelection.filter((s) => n.has(s.id));
      this.nodeDrawer.updatePositions(r);
    } else
      this.nodeDrawer.updatePositions(this.nodeSelection);
  }
  updateEdgePositions(e) {
    if (e) {
      const n = e.flatMap((o) => [...o.getEdgesOut(), ...o.getEdgesIn()]), r = new Set(n == null ? void 0 : n.map((o) => o.id)), s = this.edgeSelection.filter((o) => r.has(o.id));
      this.edgeDrawer.updatePositions(s);
    } else
      this.edgeDrawer.updatePositions(this.edgeSelection);
  }
  getNodeSelection() {
    return this.nodeSelection;
  }
  getEdgeSelection() {
    return this.edgeSelection;
  }
  // @ts-expect-error fixme: Don't really understand the typescript error below
  getGraphInteraction() {
    return this.graphInteraction;
  }
  getEventHandler() {
    return this.eventHandler;
  }
}
function tu(i, t, e) {
  const n = e.type ?? "svg";
  if (n === "svg") {
    const r = new Vd(i);
    return new Jd(i, t, r, e);
  }
  throw new Error(`\`${n}\` renderer is not implemented yet.`);
}
function eu(i = 0, t = 0, e = 1e-3) {
  let n = [], r;
  function s() {
    r = typeof e == "function" ? e : () => e;
  }
  function o(a) {
    for (let c = 0, l = n.length; c < l; ++c) {
      const h = n[c], d = r(h, c, n);
      h.vx && h.x && (h.vx -= (h.x - i) * d * a), h.vy && h.y && (h.vy -= (h.y - t) * d * a);
    }
  }
  return o.initialize = (a) => {
    n = a, s();
  }, o.x = function(a) {
    return arguments.length ? (i = a, o) : i;
  }, o.y = function(a) {
    return arguments.length ? (t = a, o) : t;
  }, o.strength = function(a) {
    return arguments.length ? (e = a, s(), o) : e;
  }, o;
}
const iu = (i, t, e, n, r) => new Promise((s, o) => {
  const a = new Worker(new URL(
    /* @vite-ignore */
    "/assets/SimulationWorker-kgekWV9K.js",
    import.meta.url
  ), {
    type: "module"
  });
  a.postMessage({ source: "simulation-worker-wrapper", nodes: i, edges: t, options: e, canvasBCR: n }), a.onmessage = (c) => {
    const { type: l, progress: h, nodes: d, edges: u, elapsedTime: p } = c.data;
    if (l === "tick" && typeof h == "number") {
      r == null || r(h, p);
      return;
    }
    l === "done" && (s({ nodes: d, edges: u }), a.terminate());
  }, a.onerror = o;
});
function nu(i) {
  var t = 0, e = i.children, n = e && e.length;
  if (!n) t = 1;
  else for (; --n >= 0; ) t += e[n].value;
  i.value = t;
}
function ru() {
  return this.eachAfter(nu);
}
function su(i, t) {
  let e = -1;
  for (const n of this)
    i.call(t, n, ++e, this);
  return this;
}
function ou(i, t) {
  for (var e = this, n = [e], r, s, o = -1; e = n.pop(); )
    if (i.call(t, e, ++o, this), r = e.children)
      for (s = r.length - 1; s >= 0; --s)
        n.push(r[s]);
  return this;
}
function au(i, t) {
  for (var e = this, n = [e], r = [], s, o, a, c = -1; e = n.pop(); )
    if (r.push(e), s = e.children)
      for (o = 0, a = s.length; o < a; ++o)
        n.push(s[o]);
  for (; e = r.pop(); )
    i.call(t, e, ++c, this);
  return this;
}
function lu(i, t) {
  let e = -1;
  for (const n of this)
    if (i.call(t, n, ++e, this))
      return n;
}
function cu(i) {
  return this.eachAfter(function(t) {
    for (var e = +i(t.data) || 0, n = t.children, r = n && n.length; --r >= 0; ) e += n[r].value;
    t.value = e;
  });
}
function hu(i) {
  return this.eachBefore(function(t) {
    t.children && t.children.sort(i);
  });
}
function du(i) {
  for (var t = this, e = uu(t, i), n = [t]; t !== e; )
    t = t.parent, n.push(t);
  for (var r = n.length; i !== e; )
    n.splice(r, 0, i), i = i.parent;
  return n;
}
function uu(i, t) {
  if (i === t) return i;
  var e = i.ancestors(), n = t.ancestors(), r = null;
  for (i = e.pop(), t = n.pop(); i === t; )
    r = i, i = e.pop(), t = n.pop();
  return r;
}
function pu() {
  for (var i = this, t = [i]; i = i.parent; )
    t.push(i);
  return t;
}
function fu() {
  return Array.from(this);
}
function gu() {
  var i = [];
  return this.eachBefore(function(t) {
    t.children || i.push(t);
  }), i;
}
function mu() {
  var i = this, t = [];
  return i.each(function(e) {
    e !== i && t.push({ source: e.parent, target: e });
  }), t;
}
function* vu() {
  var i = this, t, e = [i], n, r, s;
  do
    for (t = e.reverse(), e = []; i = t.pop(); )
      if (yield i, n = i.children)
        for (r = 0, s = n.length; r < s; ++r)
          e.push(n[r]);
  while (e.length);
}
function xi(i, t) {
  i instanceof Map ? (i = [void 0, i], t === void 0 && (t = wu)) : t === void 0 && (t = bu);
  for (var e = new _e(i), n, r = [e], s, o, a, c; n = r.pop(); )
    if ((o = t(n.data)) && (c = (o = Array.from(o)).length))
      for (n.children = o, a = c - 1; a >= 0; --a)
        r.push(s = o[a] = new _e(o[a])), s.parent = n, s.depth = n.depth + 1;
  return e.eachBefore(Cu);
}
function yu() {
  return xi(this).eachBefore(xu);
}
function bu(i) {
  return i.children;
}
function wu(i) {
  return Array.isArray(i) ? i[1] : null;
}
function xu(i) {
  i.data.value !== void 0 && (i.value = i.data.value), i.data = i.data.data;
}
function Cu(i) {
  var t = 0;
  do
    i.height = t;
  while ((i = i.parent) && i.height < ++t);
}
function _e(i) {
  this.data = i, this.depth = this.height = 0, this.parent = null;
}
_e.prototype = xi.prototype = {
  constructor: _e,
  count: ru,
  each: su,
  eachAfter: au,
  eachBefore: ou,
  find: lu,
  sum: cu,
  sort: hu,
  path: du,
  ancestors: pu,
  descendants: fu,
  leaves: gu,
  links: mu,
  copy: yu,
  [Symbol.iterator]: vu
};
function Mu(i, t) {
  return i.parent === t.parent ? 1 : 2;
}
function Hi(i) {
  var t = i.children;
  return t ? t[0] : i.t;
}
function $i(i) {
  var t = i.children;
  return t ? t[t.length - 1] : i.t;
}
function Eu(i, t, e) {
  var n = e / (t.i - i.i);
  t.c -= n, t.s += e, i.c += n, t.z += e, t.m += e;
}
function Su(i) {
  for (var t = 0, e = 0, n = i.children, r = n.length, s; --r >= 0; )
    s = n[r], s.z += t, s.m += t, t += s.s + (e += s.c);
}
function _u(i, t, e) {
  return i.a.parent === t.parent ? i.a : e;
}
function ei(i, t) {
  this._ = i, this.parent = null, this.children = null, this.A = null, this.a = this, this.z = 0, this.m = 0, this.c = 0, this.s = 0, this.t = null, this.i = t;
}
ei.prototype = Object.create(_e.prototype);
function ku(i) {
  for (var t = new ei(i, 0), e, n = [t], r, s, o, a; e = n.pop(); )
    if (s = e._.children)
      for (e.children = new Array(a = s.length), o = a - 1; o >= 0; --o)
        n.push(r = e.children[o] = new ei(s[o], o)), r.parent = e;
  return (t.parent = new ei(null, 0)).children = [t], t;
}
function Os() {
  var i = Mu, t = 1, e = 1, n = null;
  function r(l) {
    var h = ku(l);
    if (h.eachAfter(s), h.parent.m = -h.z, h.eachBefore(o), n) l.eachBefore(c);
    else {
      var d = l, u = l, p = l;
      l.eachBefore(function(x) {
        x.x < d.x && (d = x), x.x > u.x && (u = x), x.depth > p.depth && (p = x);
      });
      var g = d === u ? 1 : i(d, u) / 2, v = g - d.x, y = t / (u.x + g + v), b = e / (p.depth || 1);
      l.eachBefore(function(x) {
        x.x = (x.x + v) * y, x.y = x.depth * b;
      });
    }
    return l;
  }
  function s(l) {
    var h = l.children, d = l.parent.children, u = l.i ? d[l.i - 1] : null;
    if (h) {
      Su(l);
      var p = (h[0].z + h[h.length - 1].z) / 2;
      u ? (l.z = u.z + i(l._, u._), l.m = l.z - p) : l.z = p;
    } else u && (l.z = u.z + i(l._, u._));
    l.parent.A = a(l, u, l.parent.A || d[0]);
  }
  function o(l) {
    l._.x = l.z + l.parent.m, l.m += l.parent.m;
  }
  function a(l, h, d) {
    if (h) {
      for (var u = l, p = l, g = h, v = u.parent.children[0], y = u.m, b = p.m, x = g.m, S = v.m, C; g = $i(g), u = Hi(u), g && u; )
        v = Hi(v), p = $i(p), p.a = l, C = g.z + x - u.z - y + i(g._, u._), C > 0 && (Eu(_u(g, l, d), l, C), y += C, b += C), x += g.m, y += u.m, S += v.m, b += p.m;
      g && !$i(p) && (p.t = g, p.m += x - b), u && !Hi(v) && (v.t = u, v.m += y - S, d = l);
    }
    return d;
  }
  function c(l) {
    l.x *= t, l.y = l.depth * e;
  }
  return r.separation = function(l) {
    return arguments.length ? (i = l, r) : i;
  }, r.size = function(l) {
    return arguments.length ? (n = !1, t = +l[0], e = +l[1], r) : n ? null : [t, e];
  }, r.nodeSize = function(l) {
    return arguments.length ? (n = !0, t = +l[0], e = +l[1], r) : n ? [t, e] : null;
  }, r;
}
function we(i, t) {
  const e = {};
  for (const o of i)
    e[o.id] = [];
  for (const { source: o, target: a } of t)
    e[o.id] || (e[o.id] = []), e[o.id].push(a.id);
  const n = /* @__PURE__ */ new Set(), r = /* @__PURE__ */ new Set(), s = (o) => {
    if (!n.has(o) && (n.add(o), r.add(o), e[o]))
      for (const a of e[o]) {
        if (!n.has(a) && s(a)) return !0;
        if (r.has(a)) return !0;
      }
    return r.delete(o), !1;
  };
  return i.some((o) => s(o.id));
}
function Nr(i, t) {
  const e = new Set(t.map((n) => n.target.id));
  for (const n of i)
    if (!e.has(n.id)) return n;
  return i[0];
}
function Nu(i, t) {
  const e = /* @__PURE__ */ new Map();
  for (const c of i)
    e.set(c.id, []);
  for (const c of t)
    e.get(c.from.id) || console.log(c), e.get(c.from.id).push(c.to);
  const n = /* @__PURE__ */ new Map(), r = /* @__PURE__ */ new Map();
  function s(c, l = /* @__PURE__ */ new Set()) {
    if (r.has(c))
      return new Set(r.get(c));
    const h = /* @__PURE__ */ new Set();
    for (const d of e.get(c.id) ?? [])
      if (!l.has(d)) {
        l.add(d), h.add(d);
        const u = s(d, l);
        for (const p of u) h.add(p);
      }
    return r.set(c, h), n.set(c, h.size), h;
  }
  for (const c of i)
    n.has(c) || s(c);
  let o = null, a = -1;
  for (const c of i) {
    const l = n.get(c) ?? 0;
    l > a && (a = l, o = c);
  }
  return o ?? i[0];
}
function Au(i, t) {
  const e = /* @__PURE__ */ new Map(), n = /* @__PURE__ */ new Map();
  for (const l of i)
    e.set(l.id, []), n.set(l.id, 0);
  for (const l of t)
    l.directed !== !1 && (e.get(l.from.id).push(l.to), n.set(l.to.id, (n.get(l.to.id) || 0) + 1));
  const r = [], s = i.filter((l) => n.get(l.id) === 0);
  for (; s.length; ) {
    const l = s.shift();
    r.push(l);
    for (const h of e.get(l.id))
      n.set(h.id, n.get(h.id) - 1), n.get(h.id) === 0 && s.push(h);
  }
  if (r.length !== i.length)
    return console.warn("Graph has a cycle! Min-max distance root undefined."), i[0];
  const o = /* @__PURE__ */ new Map();
  for (let l = r.length - 1; l >= 0; l--) {
    const h = r[l];
    let d = 0;
    for (const u of e.get(h.id))
      d = Math.max(d, 1 + (o.get(u.id) || 0));
    o.set(h.id, d);
  }
  let a = null, c = 1 / 0;
  for (const l of i) {
    const h = o.get(l.id);
    h < c && (c = h, a = l);
  }
  return a ?? i[0];
}
function Iu(i, t) {
  const e = /* @__PURE__ */ new Map(), n = /* @__PURE__ */ new Map();
  for (const l of i)
    e.set(l.id, []), n.set(l.id, 0);
  for (const l of t)
    l.directed !== !1 && (e.get(l.from.id).push(l.to), n.set(l.to.id, (n.get(l.to.id) || 0) + 1));
  const r = [], s = i.filter((l) => n.get(l.id) === 0);
  for (; s.length; ) {
    const l = s.shift();
    r.push(l);
    for (const h of e.get(l.id))
      n.set(h.id, n.get(h.id) - 1), n.get(h.id) === 0 && s.push(h);
  }
  if (r.length !== i.length)
    return console.warn("Graph has a cycle! Cannot minimize DAG height."), i[0];
  const o = /* @__PURE__ */ new Map();
  for (let l = r.length - 1; l >= 0; l--) {
    const h = r[l];
    let d = 0;
    for (const u of e.get(h.id))
      d = Math.max(d, 1 + (o.get(u.id) ?? 0));
    o.set(h.id, d);
  }
  let a = null, c = 1 / 0;
  for (const l of i) {
    const h = o.get(l.id);
    h < c && (c = h, a = l);
  }
  return a ?? i[0];
}
const Gi = {
  type: "tree",
  rootId: void 0,
  rootIdAlgorithmFinder: "MaxReachability",
  strength: 0.25,
  radial: !1,
  radialGap: 750,
  horizontal: !1,
  flipEdgeDirection: !1
};
class At {
  constructor(t, e, n, r = {}) {
    f(this, "graph");
    f(this, "simulation");
    f(this, "simulationForces");
    f(this, "options");
    f(this, "originalForceStrength");
    f(this, "canvasBCR");
    f(this, "levels");
    f(this, "positionedNodesByID");
    this.graph = t, this.simulation = e, this.simulationForces = n, this.options = re({}, Gi, r), this.originalForceStrength = {
      link: this.simulationForces.link.strength(),
      charge: this.simulationForces.charge.strength(),
      center: this.simulationForces.center.strength(),
      gravity: this.simulationForces.gravity.strength()
    }, this.positionedNodesByID = /* @__PURE__ */ new Map(), this.levels = {};
    const s = this.graph.getNodes(), o = this.options.flipEdgeDirection ? this.flipEdgeDirection(this.graph.getEdges()) : this.graph.getEdges();
    if (we(s, o)) {
      this.graph.notifier.warning("Tree layout unavailable", "The graph contains a cycle, so it cannot be displayed as a tree.");
      return;
    }
    this.setSizes(), this.update(), this.registerForces();
  }
  update() {
    const t = this.graph.getNodes(), e = this.options.flipEdgeDirection ? this.flipEdgeDirection(this.graph.getEdges()) : this.graph.getEdges(), { levels: n } = At.buildLevels(t, e, void 0, this.options.rootIdAlgorithmFinder), { nodes: r, nodeById: s } = At.buildTree(t, e, this.options, this.canvasBCR);
    this.positionedNodesByID = s, this.levels = n, r && this.setNodePositions(r, this.options);
  }
  flipEdgeDirection(t) {
    return t.forEach((e) => {
      const n = e.from;
      e.setFrom(e.to), e.setTo(n);
    }), t;
  }
  setSizes() {
    const t = this.graph.renderer.getCanvas();
    if (!t)
      throw new Error("Canvas element is not defined in the graph renderer.");
    this.canvasBCR = t.getBoundingClientRect();
  }
  setNodePositions(t, e) {
    for (const n of t) {
      const r = this.graph.getMutableNode(n.data.id);
      if (r)
        if (e.radial) {
          const s = n.x ?? 0, o = n.y ?? 0;
          r.x = o * Math.cos(s - Math.PI / 2), r.y = o * Math.sin(s - Math.PI / 2), r.fx = r.x, r.fy = r.y;
        } else e.horizontal ? (r.x = n.y, r.fx = n.y, r.y = n.x, delete r.fy) : (r.x = n.x, r.y = n.y, r.fy = n.y, delete r.fx);
    }
  }
  unsetNodePositions() {
    this.graph.getMutableNodes().forEach((t) => {
      delete t.fy, delete t.fx;
    });
  }
  registerForces() {
    const t = this.options.strength ?? 0.1;
    if (this.options.radial) {
      const e = Mr(
        (n) => (this.levels[n.id] ?? 1) * 100,
        0,
        0
      ).strength(t);
      this.simulation.force("tree-radial", e);
    } else
      this.simulation.force("tree-y", Sr((e) => {
        var n, r;
        return this.options.horizontal ? ((n = this.positionedNodesByID.get(e.id)) == null ? void 0 : n.x) ?? 0 : ((r = this.positionedNodesByID.get(e.id)) == null ? void 0 : r.y) ?? 0;
      }).strength(t)), this.simulation.force("tree-x", Er((e) => {
        var n, r;
        return this.options.horizontal ? ((n = this.positionedNodesByID.get(e.id)) == null ? void 0 : n.y) ?? 0 : ((r = this.positionedNodesByID.get(e.id)) == null ? void 0 : r.x) ?? 0;
      }).strength(t));
    At.adjustOtherSimulationForces(this.simulationForces, this.options);
  }
  unregisterLayout() {
    this.unregisterForces(), this.unsetNodePositions();
  }
  unregisterForces() {
    this.simulation.force("tree-radial", null), this.simulation.force("tree-y", null), this.simulation.force("tree-x", null), At.resetOtherSimulationForces(this.simulationForces, this.originalForceStrength);
  }
  static registerForcesOnSimulation(t, e, n, r, s, o, a = this) {
    const c = re({}, Gi, s), l = c.strength ?? 0.1, h = o.width, d = o.height, u = [h / 2, d / 2];
    if (we(t, e))
      return;
    const { levels: p } = a.buildLevels(t, e, void 0, c.rootIdAlgorithmFinder), { nodeById: g } = a.buildTree(t, e, c, o);
    if (c.radial) {
      const v = Mr(
        (y) => (p[y.id] ?? 1) * 100,
        u[0],
        u[1]
      ).strength(l);
      n.force("tree-radial", v);
    } else
      n.force("tree-y", Sr((v) => {
        var y, b;
        return c.horizontal ? ((y = g.get(v.id)) == null ? void 0 : y.x) ?? 0 : ((b = g.get(v.id)) == null ? void 0 : b.y) ?? 0;
      }).strength(l)), n.force("tree-x", Er((v) => {
        var y, b;
        return c.horizontal ? ((y = g.get(v.id)) == null ? void 0 : y.y) ?? 0 : ((b = g.get(v.id)) == null ? void 0 : b.x) ?? 0;
      }).strength(l));
    a.adjustOtherSimulationForces(r, c);
  }
  static adjustOtherSimulationForces(t, e) {
    e != null && e.radial ? (t.link.strength(0), t.charge.strength(0), t.center.strength(0), t.gravity.strength(0)) : (t.link.strength(0), t.charge.strength(0), t.gravity.strength(1e-5), t.center.strength(1e-5));
  }
  static resetOtherSimulationForces(t, e) {
    t.link.strength(e.link), t.charge.strength(e.charge), t.center.strength(e.center), t.gravity.strength(e.gravity);
  }
  static simulationDone(t, e, n, r) {
    const s = re({}, Gi, r);
    for (const o of t)
      s.radial ? (o.fx = o.x, o.fy = o.y) : s.horizontal ? (o.fx = o.x, delete o.fy) : (o.fy = o.y, delete o.fx);
  }
  static buildTree(t, e, n, r) {
    if (!t.length)
      return {
        root: null,
        nodes: [],
        nodeById: /* @__PURE__ */ new Map()
      };
    if (we(t, e))
      return console.warn("Cycle detected in graph. Tree layout will not be computed."), {
        root: null,
        nodes: [],
        nodeById: /* @__PURE__ */ new Map()
      };
    const s = /* @__PURE__ */ new Map();
    for (const v of t) {
      const y = v;
      y.children = [], s.set(v.id, y);
    }
    for (const v of e) {
      const y = s.get(v.source.id), b = s.get(v.target.id);
      y && b && (y.children.push(b), b.parent = y);
    }
    const o = n.rootId || At.findRootId(t, e, n.rootIdAlgorithmFinder), a = s.get(o);
    if (!a)
      throw new Error(`Root node with id "${o}" not found.`);
    const c = n.radialGap, l = n.radial ? 2 * Math.PI : r.width, h = n.radial ? c : r.height, d = Os();
    n.radial ? d.size([l, h]) : d.size([l, h]).separation((v, y) => {
      var x, S;
      const b = ((S = (x = v.parent) == null ? void 0 : x.children) == null ? void 0 : S.length) ?? 1;
      return v.parent === y.parent ? 1.5 / b : 1.5;
    });
    const u = xi(a), p = d(u), g = /* @__PURE__ */ new Map();
    return p.descendants().forEach((v) => {
      g.set(v.data.id, v);
    }), {
      root: p,
      nodes: p.descendants(),
      nodeById: g
    };
  }
  /**
   * Builds a mapping from node ID to its level (distance from the root),
   * by traversing the graph in BFS manner. If the graph contains cycles,
   * each node is assigned the shortest level found first.
   *
   * @param nodes - The list of graph nodes.
   * @param edges - The list of graph edges (assumed to be directed).
   * @param passedRootId - The ID of the node considered as the root.
   * @param rootIdAlgorithmFinder - The algorithm to use to find the root ID.
   * @returns A mapping of each node's ID to its depth level in the tree and the maximum depth
   */
  static buildLevels(t, e, n, r) {
    if (!t.length)
      return {
        levels: {},
        maxDepth: 0,
        nodeCountPerLevel: {}
      };
    const s = n || At.findRootId(t, e, r), o = { [s]: 0 }, a = {};
    for (const u of t)
      a[u.id] = [];
    for (const { source: u, target: p } of e)
      a[u.id].push(p.id);
    const c = [s];
    let l = 0;
    for (; l < c.length; ) {
      const u = c[l++], p = o[u];
      for (const g of a[u] || [])
        g in o || (o[g] = p + 1, c.push(g));
    }
    const h = Math.max(...Object.values(o)), d = {};
    for (const u of Object.values(o))
      d[u] = (d[u] || 0) + 1;
    return {
      levels: o,
      maxDepth: h,
      nodeCountPerLevel: d
    };
  }
  /**
   * Attempts to infer the root node of a directed graph.
   *
   * This function looks for a node that is never a target in the list of links,
   * assuming such a node is a likely root (i.e., has no incoming edges).
   * If no such node is found, it falls back to the first node in the list.
   *
   * @param nodes - The list of graph nodes.
   * @param edges - The list of graph edges (assumed to be directed).
   * @returns The ID of the inferred root node.
   */
  static findRootId(t, e, n) {
    switch (n) {
      case "FirstZeroInDegree":
        return Nr(t, e).id;
      case "MaxReachability":
        return Nu(t, e).id;
      case "MinMaxDistance":
        return Au(t, e).id;
      case "MinHeight":
        return Iu(t, e).id;
      default:
        return Nr(t, e).id;
    }
  }
}
class Lu extends At {
  constructor(t, e, n, r) {
    super(t, e, n, {
      ...r,
      type: "tree"
    });
  }
  buildTree(t, e, n, r) {
    if (!t.length)
      return {
        root: null,
        nodes: [],
        nodeById: /* @__PURE__ */ new Map()
      };
    if (we(t, e))
      return console.warn("Cycle detected in graph. Tree layout will not be computed."), {
        root: null,
        nodes: [],
        nodeById: /* @__PURE__ */ new Map()
      };
    const s = /* @__PURE__ */ new Map();
    for (const v of t) {
      const y = v;
      y.children = [], s.set(v.id, y);
    }
    if (!n.rootId || !s.get(n.rootId))
      throw new Error("Ego Tree can only be created with a rootId");
    const o = n.rootId, a = s.get(o);
    if (a.children = [], !a)
      throw new Error(`Root node with id "${o}" not found.`);
    for (const v of e) {
      const y = s.get(v.source.id), b = s.get(v.target.id);
      y && b && (v.source.id === a.id ? (a.children.push(b), b.parent = a) : v.target.id === a.id && (a.children.push(y), y.parent = a));
    }
    const c = n.radialGap, l = n.radial ? 2 * Math.PI : r.width, h = n.radial ? c : r.height, d = Os();
    n.radial ? d.size([l, h]) : d.size([l, h]).separation((v, y) => {
      var x, S;
      const b = ((S = (x = v.parent) == null ? void 0 : x.children) == null ? void 0 : S.length) ?? 1;
      return v.parent === y.parent ? 1.5 / b : 1.5;
    });
    const u = xi(a), p = d(u), g = /* @__PURE__ */ new Map();
    return p.descendants().forEach((v) => {
      g.set(v.data.id, v);
    }), {
      root: p,
      nodes: p.descendants(),
      nodeById: g
    };
  }
}
function Ou(i = 0, t = 0, e = 1e-3, n = () => !0) {
  let r = [];
  function s() {
    if (!r.length) return;
    let o = 0, a = 0, c = 0;
    r.forEach((l, h) => {
      n(l, h, r) && (l.x == null || l.y == null || (o += l.x, a += l.y, c++));
    }), c && (o = (o / c - i) * e, a = (a / c - t) * e, r.forEach((l, h) => {
      n(l, h, r) && (l.x == null || l.y == null || (l.x -= o, l.y -= a));
    }));
  }
  return s.initialize = (o) => {
    r = o;
  }, s.x = function(o) {
    return arguments.length ? (i = o, s) : i;
  }, s.y = function(o) {
    return arguments.length ? (t = o, s) : t;
  }, s.strength = function(o) {
    return arguments.length ? (e = o, s) : e;
  }, s.filter = function(o) {
    return arguments.length ? (n = o, s) : n;
  }, s;
}
const Vt = {
  d3Alpha: 1,
  d3AlphaMin: 1e-3,
  d3AlphaDecay: 0.05,
  d3AlphaTarget: 0,
  d3VelocityDecay: 0.45,
  d3LinkDistance: 40,
  d3LinkStrength: null,
  d3ManyBodyStrength: -150,
  d3ManyBodyTheta: 0.9,
  d3CollideRadius: 12,
  d3CollideStrength: 1,
  d3CollideIterations: 1,
  d3CenterStrength: 1,
  d3GravityStrength: 0.01,
  enabled: !0,
  cooldownTime: 2e3,
  useWorker: !0,
  warmupTicks: "auto",
  freezeNodesOnDrag: !0,
  layout: {
    type: "force"
  },
  callbacks: {
    onInit: () => {
    },
    onStart: () => {
    },
    onStop: () => {
    },
    onTick: () => {
    }
  }
};
class ee {
  constructor(t, e = {}) {
    f(this, "simulation");
    f(this, "graph");
    f(this, "canvas");
    f(this, "graphInteraction");
    f(this, "layout");
    f(this, "canvasBCR");
    f(this, "animationFrameId", null);
    f(this, "startSimulationTime", 0);
    f(this, "engineRunning", !1);
    f(this, "slowTickThresholdReached", !1);
    f(this, "lastTickTime", 0);
    f(this, "avgTickDuration", 0);
    f(this, "SLOW_TICK_THRESHOLD", 50);
    // ms (20fps budget)
    f(this, "dragInProgress", !1);
    f(this, "dragSelection", []);
    f(this, "totalTickCount", 0);
    f(this, "options");
    f(this, "callbacks");
    f(this, "simulationForces");
    f(this, "scaledForces", {
      d3ManyBodyStrength: Vt.d3ManyBodyStrength,
      d3CollideStrength: Vt.d3CollideStrength
    });
    if (this.graph = t, this.options = re({}, Vt, e), this.callbacks = this.options.callbacks ?? {}, this.canvas = this.graph.renderer.getCanvas(), !this.canvas) throw new Error("Canvas element is not defined in the graph renderer.");
    if (this.canvasBCR = this.canvas.getBoundingClientRect(), this.graphInteraction = this.graph.renderer.getGraphInteraction(), !this.graphInteraction) throw new Error("Graph interaction is not available.");
    const n = ee.initSimulationForces(this.options, this.canvasBCR);
    this.simulation = n.simulation, this.simulationForces = n.simulationForces, this.scaledForces.d3ManyBodyStrength = this.options.d3ManyBodyStrength || Vt.d3ManyBodyStrength, this.scaledForces.d3CollideStrength = this.options.d3CollideStrength || Vt.d3CollideStrength, this.options.layout.type === "tree" ? this.layout = new At(
      this.graph,
      this.simulation,
      this.simulationForces,
      this.options.layout
    ) : this.options.layout.type === "egoTree" && (this.layout = new Lu(
      this.graph,
      this.simulation,
      this.simulationForces,
      this.options.layout
    )), this.callbacks.onInit && this.callbacks.onInit(this);
  }
  /** @private */
  static initSimulationForces(t, e) {
    const n = {
      link: vd(),
      charge: _d(),
      center: Ou(),
      collide: gd(),
      gravity: eu()
      // clusterRadialConstraint: ForceClusterRadial(),
    }, r = Sd().force("link", n.link).force("charge", n.charge).force("center", n.center).force("collide", n.collide).force("gravity", n.gravity);
    return this.initSimulationForceCenter(n.center, t), this.initSimulationForceGravity(n.gravity, t, e), this.initSimulationForceLink(n.link, t), this.initSimulationForceCharge(n.charge, t), this.initSimulationForceCollide(n.collide, t), r.alphaMin(t.d3AlphaMin), r.alphaDecay(t.d3AlphaDecay), r.alphaTarget(0), r.velocityDecay(t.d3VelocityDecay), {
      simulation: r,
      simulationForces: n
    };
  }
  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  static initSimulationForceCenter(t, e) {
    t.x(0).y(0).strength(0.05).filter((n) => !n.isChild);
  }
  static initSimulationForceGravity(t, e, n) {
    t.x(n.width / 2).y(n.height / 2).strength((r) => (r.degree() ?? 0) === 0 ? e.d3GravityStrength : 0);
  }
  static initSimulationForceLink(t, e) {
    t.distance((n) => {
      const r = Ls(n);
      if (!r || r === "")
        return e.d3LinkDistance;
      const s = r.length * 10;
      return Math.max(e.d3LinkDistance, s);
    }), e.d3LinkStrength && t.strength(e.d3LinkStrength);
  }
  static initSimulationForceCharge(t, e) {
    t.theta(e.d3ManyBodyTheta).strength((n) => {
      const r = n, s = e.d3ManyBodyStrength, o = r.getCircleRadius(), a = 10 + Math.sqrt(o - 10);
      let c = r.weight ?? 1;
      return c *= r.isParent ? 10 : 1, s * (a * a) / 100 * c;
    });
  }
  static initSimulationForceCollide(t, e) {
    t.radius((n) => {
      const r = n;
      return r.expanded ? 1.2 * r.getCircleRadius() + 20 : r.getCircleRadius() ? 1.2 * r.getCircleRadius() : e.d3CollideRadius;
    }).strength(e.d3CollideStrength);
  }
  static initSimulationForceClusterRadialConstraint(t, e) {
    t.strength(e.d3CollideStrength);
  }
  update() {
    this.layout && this.layout.update();
    const t = this.graph.getMutableNodes().filter((n) => n.visible);
    this.simulation.nodes(t);
    const e = this.simulation.force("link");
    e && e.id((n) => n.id).links(this.getActiveEdges()), this.restart();
  }
  /** @private */
  getActiveEdges() {
    const t = this.graph.getMutableEdges().filter((n) => {
      if (!n.visible) return !1;
      const r = n.source, s = n.target;
      return !(r.isChild || s.isChild);
    }), e = this.getClusterLinks();
    return [...t, ...e];
  }
  /** @private */
  getClusterLinks() {
    return this.graph.getMutableEdges().filter((e) => e.visible);
  }
  /** @private */
  scaleSimulationOptions() {
    const t = ee.scaleSimulationOptions(this.options, this.canvasBCR, this.graph.getNodeCount());
    this.scaledForces.d3ManyBodyStrength = t.d3ManyBodyStrength ?? Vt.d3ManyBodyStrength, this.scaledForces.d3CollideStrength = t.d3CollideStrength ?? Vt.d3CollideStrength;
  }
  /** @private */
  static scaleSimulationOptions(t, e, n) {
    const r = n / (e.width * e.height), s = Math.min(2, 75e-6 / r);
    return {
      d3ManyBodyStrength: t.d3ManyBodyStrength * s,
      d3CollideStrength: t.d3ManyBodyStrength * s
    };
  }
  /** @private */
  applyScalledSimulationOptions() {
    ee.initSimulationForceCharge(this.simulationForces.charge, this.options), ee.initSimulationForceCollide(this.simulationForces.collide, this.options);
  }
  enable() {
    this.avgTickDuration = 0, this.options.enabled = !0, this.start(!1);
  }
  disable() {
    this.options.enabled = !1, this.stop();
  }
  /**
   * Pause the simulation
   */
  pause() {
    this.engineRunning = !1, this.slowTickThresholdReached = !1;
  }
  /**
   * Restart the simulation with rendering on each animation frame.
   */
  restart() {
    this.startSimulationTime = (/* @__PURE__ */ new Date()).getTime(), this.lastTickTime = performance.now(), this.engineRunning = !0, this.slowTickThresholdReached = !1;
  }
  /**
   * Start the simulation with rendering on each animation frame.
   */
  async start(t = !0) {
    if (t && await this.runSimulationWorkerRouter(), !this.options.enabled) {
      this.engineRunning = !1;
      return;
    }
    this.lastTickTime = performance.now(), this.engineRunning = !0, this.slowTickThresholdReached = !1, this.callbacks.onStart && this.callbacks.onStart(this), this.animationFrameId === null && this.startAnimationLoop();
  }
  /**
   * Manually stop the simulation and cancel animation frame.
   */
  stop() {
    this.engineRunning = !1, this.animationFrameId !== null && (cancelAnimationFrame(this.animationFrameId), this.animationFrameId = null), this.simulation.stop(), this.callbacks.onStop && this.callbacks.onStop(this);
  }
  /**
   * Start the simulation loop with rendering on each animation frame.
   */
  startAnimationLoop() {
    const t = () => {
      this.animationFrameId = requestAnimationFrame(t), this.simulationTick();
    };
    this.engineRunning = !0, this.simulation.alpha(0.01).restart(), this.animationFrameId = requestAnimationFrame(t);
  }
  /**
   * Evaluate at each tick to update the simulation state and request rendering
   */
  simulationTick() {
    this.engineRunning && (!this.dragInProgress && ((/* @__PURE__ */ new Date()).getTime() - this.startSimulationTime > this.options.cooldownTime || this.options.d3AlphaMin > 0 && this.simulation.alpha() < this.options.d3AlphaMin) && (this.engineRunning = !1, this.simulation.stop(), this.callbacks.onStop && this.callbacks.onStop(this)), this.totalTickCount++, this.updateTickMetrics(), this.simulation.tick(), this.graph.nextTick(), this.callbacks.onTick && this.callbacks.onTick(this), this.graphInteraction.simulationTick(), this.totalTickCount % 10 === 0 && this.graphInteraction.simulationSlowTick());
  }
  updateTickMetrics() {
    var n;
    const t = performance.now(), e = t - this.lastTickTime;
    this.lastTickTime = t, this.avgTickDuration = this.avgTickDuration * 0.9 + e * 0.1, this.avgTickDuration > this.SLOW_TICK_THRESHOLD && (this.slowTickThresholdReached = !0, this.disable(), (n = this.graph.UIManager.graphControls) == null || n.updatePhysicSimulationIndicator(!1), this.graph.UIManager.showNotification({
      level: "warning",
      title: "Physics engine running slow",
      message: "The physic has been disabled."
    }));
  }
  /**
   * Returns a promise that resolves when the simulation stops naturally.
   * Useful for performing actions (like fitAndCenter) after stabilization.
   */
  async waitForSimulationStop() {
    if (this.engineRunning)
      return new Promise((t) => {
        const e = this.callbacks.onStop;
        this.callbacks.onStop = (n) => {
          e == null || e(n), this.callbacks.onStop = e, t();
        };
      });
  }
  isEnabled() {
    return this.options.enabled;
  }
  async computeGraph(t = {}) {
    var h;
    const { runSimulation: e } = await import("./SimulationWorker-C-vOCtWl.js"), n = (h = this.canvas) == null ? void 0 : h.getBoundingClientRect();
    if (!n) return;
    const r = this.graph.getMutableNodes(), s = this.graph.getNodes().map((d) => (d.fx = void 0, d.fy = void 0, d)), o = this.graph.getEdges(), { callbacks: a, ...c } = this.options;
    Object.assign(c, t);
    const { nodes: l } = e(
      s,
      o,
      c,
      n
    );
    l.forEach((d, u) => {
      r[u].x = d.x, r[u].y = d.y, d.fx ? r[u].fx = d.fx : r[u].fx = void 0, d.fy ? r[u].fy = d.fy : r[u].fy = void 0;
    }), this.graph.updateData(r, void 0, !1);
  }
  async runSimulationWorkerRouter(t = {}) {
    this.options.useWorker ? await this.runSimulationWorker(t) : (await this.computeGraph(t), this.graph.updateLayoutProgress(100, 0, "done"));
  }
  async runSimulationWorker(t = {}) {
    var h;
    const e = (h = this.canvas) == null ? void 0 : h.getBoundingClientRect();
    if (!e) return;
    const n = this.graph.getMutableNodes(), r = this.graph.getNodes().map((d) => (d.fx = void 0, d.fy = void 0, d)), s = this.graph.getEdges(), o = (d, u) => {
      this.graph.updateLayoutProgress(d, u, "simulation");
    }, { callbacks: a, ...c } = this.options;
    Object.assign(c, t);
    const { nodes: l } = await iu(
      r,
      s,
      c,
      e,
      o
    );
    this.graph.updateLayoutProgress(100, 0, "rendering"), l.forEach((d, u) => {
      n[u].x = d.x, n[u].y = d.y, d.fx ? n[u].fx = d.fx : n[u].fx = void 0, d.fy ? n[u].fy = d.fy : n[u].fy = void 0;
    }), this.graph.updateData(n, void 0, !1), this.graph.updateLayoutProgress(100, 0, "done");
  }
  /**
   * Restart the simulation with a bit of heat
   */
  reheat(t = 0.7) {
    this.restart(), this.simulation.alpha(t).restart();
  }
  /**
   * @private
   */
  createDragBehavior() {
    return Gh().on("start.draggedelement", (t, e) => {
      this.graphInteraction.hasActiveMultiselection() ? this.dragSelection = this.graphInteraction.getSelectedNodes().map((n) => {
        const { node: r } = n;
        return r.freeze(), {
          node: r,
          dx: r.x - e.x,
          dy: r.y - e.y
        };
      }) : (this.dragSelection = [], e.freeze());
    }).on("drag.draggedelement", (t, e) => {
      if (!this.dragInProgress && this.isEnabled() && (this.dragInProgress = !0, this.restart(), this.simulation.alphaTarget(0.3).restart()), this.graphInteraction.hasActiveMultiselection() ? this.dragSelection.forEach(({ node: n, dx: r, dy: s }) => {
        n.fx = t.x + r, n.fy = t.y + s, n.x = t.x + r, n.y = t.y + s;
      }) : (e.fx = t.x, e.fy = t.y, e.x = t.x, e.y = t.y), this.graphInteraction.dragging(t.sourceEvent, t.subject), !this.engineRunning || !this.isEnabled()) {
        const n = this.graphInteraction.hasActiveMultiselection() ? this.dragSelection.map((r) => r.node) : [e];
        this.graph.nextTickFor(n);
      }
    }).on("end.draggedelement", (t, e) => {
      !t.active && this.dragInProgress && (this.dragInProgress = !1, this.restart(), this.simulation.alphaTarget(this.options.d3AlphaTarget).restart()), this.options.freezeNodesOnDrag || (this.graphInteraction.hasActiveMultiselection() ? (this.dragSelection.forEach(({ node: n }) => n.unfreeze()), this.dragSelection = []) : e.unfreeze()), this.graphInteraction.dragended(t.sourceEvent, t.subject);
    });
  }
  isDragging() {
    return this.dragInProgress;
  }
  getForceSimulation() {
    return this.simulationForces;
  }
  getSimulation() {
    return this.simulation;
  }
  /**
   * Allows to change the layout of the graph
   * 
   * @example
   * ```ts
   * changeLayout('tree', {
   *     layout: {
   *          horizontal: false,
   *          rootIdAlgorithmFinder: 'FirstZeroInDegree'
   *     }
   * })
   * ```
   */
  async changeLayout(t, e = {}) {
    var n;
    this.layout && ((n = this.layout) == null || n.unregisterLayout(), this.layout = void 0), e = e ?? {}, e.layout = e.layout ?? {}, e.layout.type = t, t === "force" ? this.applyScalledSimulationOptions() : t === "tree" && (this.layout = new At(this.graph, this.simulation, this.simulationForces, e.layout)), this.options.layout.type = t, this.update(), this.pause(), await this.runSimulationWorkerRouter(e), this.restart(), await this.waitForSimulationStop(), this.graph.renderer.fitAndCenter();
  }
}
const Tu = '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24"><path fill="currentColor" d="M18 3a3 3 0 0 1 2.995 2.824L21 6v12a3 3 0 0 1-2.824 2.995L18 21H6a3 3 0 0 1-2.995-2.824L3 18V6a3 3 0 0 1 2.824-2.995L6 3zm0 2H9v14h9a1 1 0 0 0 .993-.883L19 18V6a1 1 0 0 0-.883-.993zm-4.387 4.21l.094.083l2 2a1 1 0 0 1 .083 1.32l-.083.094l-2 2a1 1 0 0 1-1.497-1.32l.083-.094L13.585 12l-1.292-1.293a1 1 0 0 1-.083-1.32l.083-.094a1 1 0 0 1 1.32-.083"/></svg>', Pu = '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24"><path fill="currentColor" d="M18 3a3 3 0 0 1 2.995 2.824L21 6v12a3 3 0 0 1-2.824 2.995L18 21H6a3 3 0 0 1-2.995-2.824L3 18V6a3 3 0 0 1 2.824-2.995L6 3zm-3 2H6a1 1 0 0 0-.993.883L5 6v12a1 1 0 0 0 .883.993L6 19h9zm-3.293 4.293a1 1 0 0 1 .083 1.32l-.083.094L10.415 12l1.292 1.293a1 1 0 0 1 .083 1.32l-.083.094a1 1 0 0 1-1.32.083l-.094-.083l-2-2a1 1 0 0 1-.083-1.32l.083-.094l2-2a1 1 0 0 1 1.414 0"/></svg>', Du = '<svg width="4.2333331mm" height="3.96875mm" viewBox="0 0 4.2333331 3.96875" version="1.1" id="svg1" xmlns="http://www.w3.org/2000/svg" xmlns:svg="http://www.w3.org/2000/svg"> <defs id="defs1" /> <g id="layer1" transform="translate(-132.29166,-106.89167)"> <path fill="currentColor" fill-rule="evenodd" d="m 132.57451,108.09552 a 0.66066458,0.66066458 0 0 0 1.04007,-0.54239 0.66145833,0.66145833 0 1 0 -1.04007,0.54239 m 0.37861,-0.27781 a 0.264585,0.264585 0 1 0 0,-0.52917 0.264585,0.264585 0 0 0 0,0.52917 m 2.91042,0.39687 a 0.66066458,0.66066458 0 0 1 -0.66146,-0.66145 0.66145833,0.66145833 0 1 1 0.66146,0.66145 m 0.26458,-0.66145 a 0.26458333,0.26458333 0 1 1 -0.52916,0 0.26458333,0.26458333 0 0 1 0.52916,0 m -2.2307,1.33614 a 0.66066458,0.66066458 0 0 0 1.04008,-0.54239 0.66145833,0.66145833 0 1 0 -1.04008,0.54239 m 0.37862,-0.27781 a 0.264585,0.264585 0 1 0 0,-0.52917 0.264585,0.264585 0 0 0 0,0.52917 m 1.19063,1.71979 a 0.66066458,0.66066458 0 0 1 -0.66146,-0.66146 0.66145833,0.66145833 0 1 1 0.66146,0.66146 m 0.26458,-0.66146 a 0.264585,0.264585 0 1 1 -0.52917,0 0.264585,0.264585 0 0 1 0.52917,0 m -2.24896,1.19063 a 0.66066458,0.66066458 0 0 1 -0.66146,-0.66146 0.66145833,0.66145833 0 1 1 0.66146,0.66146 m 0.26458,-0.66146 a 0.26458333,0.26458333 0 1 1 -0.52916,0 0.26458333,0.26458333 0 0 1 0.52916,0" clip-rule="evenodd" id="path1" style="stroke-width:0.264583" /> <path fill="none" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round" stroke-width="0.529167" d="m 133.06292,108.11741 0.25132,1.51998 m 0.7969,-0.73919 -0.3281,0.80361 m 1.57769,-1.87938 -0.59147,0.26106 m 0.35159,1.16811 -0.45978,-0.53433" id="path1-6" /> </g> </svg>', Fu = `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24">
    <path fill="none" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 20a2 2 0 1 0-4 0a2 2 0 0 0 4 0M16 4a2 2 0 1 0-4 0a2 2 0 0 0 4 0m0 16a2 2 0 1 0-4 0a2 2 0 0 0 4 0m-5-8a2 2 0 1 0-4 0a2 2 0 0 0 4 0m10 0a2 2 0 1 0-4 0a2 2 0 0 0 4 0M5.058 18.306l2.88-4.606m2.123-3.397l2.877-4.604m-2.873 8.006l2.876 4.6M15.063 5.7l2.881 4.61" />
</svg>`, zu = `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" style="transform: rotate(-90deg);">
    <path fill="none" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 20a2 2 0 1 0-4 0a2 2 0 0 0 4 0M16 4a2 2 0 1 0-4 0a2 2 0 0 0 4 0m0 16a2 2 0 1 0-4 0a2 2 0 0 0 4 0m-5-8a2 2 0 1 0-4 0a2 2 0 0 0 4 0m10 0a2 2 0 1 0-4 0a2 2 0 0 0 4 0M5.058 18.306l2.88-4.606m2.123-3.397l2.877-4.604m-2.873 8.006l2.876 4.6M15.063 5.7l2.881 4.61" />
</svg>`, Bu = `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24">
    <path fill="none" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 19a2 2 0 1 0-4 0a2 2 0 0 0 4 0m8-14a2 2 0 1 0-4 0a2 2 0 0 0 4 0m-8 0a2 2 0 1 0-4 0a2 2 0 0 0 4 0m-4 7a2 2 0 1 0-4 0a2 2 0 0 0 4 0m12 7a2 2 0 1 0-4 0a2 2 0 0 0 4 0m-4-7a2 2 0 1 0-4 0a2 2 0 0 0 4 0m8 0a2 2 0 1 0-4 0a2 2 0 0 0 4 0M6 12h4m4 0h4m-3-5l-2 3M9 7l2 3m0 4l-2 3m4-3l2 3" />
</svg>`, Ru = '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24"><path fill="none" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 15h2a1.5 1.5 0 0 0 0-3h-2V9h3.5M3 12v.01M21 12v.01M12 21v.01M7.5 4.2v.01m9 15.59v.01m-9-.01v.01M4.2 16.5v.01m15.6-.01v.01m0-9.01v.01M4.2 7.5v.01m12.3-3.304A9.04 9.04 0 0 0 12 3"/></svg>', Hu = '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24"><path fill="none" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 9v6m3-4v2a2 2 0 1 0 4 0v-2a2 2 0 1 0-4 0m-9 1v.01M21 12v.01M12 21v.01M7.5 4.2v.01m9 15.59v.01m-9-.01v.01M4.2 16.5v.01m15.6-.01v.01M4.2 7.5v.01m15.61.017A9 9 0 0 0 12 3"/></svg>', $u = '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24"><path fill="none" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 15h2a1 1 0 0 0 1-1v-1a1 1 0 0 0-1-1h-2V9h3M9 9v6m-6-3v.01M12 21v.01M7.5 4.2v.01m9 15.59v.01m-9-.01v.01M4.2 16.5v.01m15.6-.01v.01M4.2 7.5v.01M21 12a9 9 0 0 0-9-9"/></svg>', qi = '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 20 20"><path fill="currentColor" d="M15.72 2.22a.75.75 0 1 1 1.06 1.06l-.97.97l.97.97a.75.75 0 0 1-1.06 1.06l-1.5-1.5a.75.75 0 0 1 0-1.06zM3.75 3.5h7.5a.75.75 0 0 1 0 1.5h-7.5a.75.75 0 0 1 0-1.5m12.5 10a.75.75 0 0 1 0 1.5H3.75a.75.75 0 0 1 0-1.5zM3.75 10h12.5a.75.75 0 0 0 0-1.5H3.75a.75.75 0 0 0 0 1.5"/></svg>', Vi = '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 32 32"><path fill="currentColor" d="M10 15h12v2H10zM8.7 6.285A3 3 0 0 0 9 5a3 3 0 1 0-3 3a2.96 2.96 0 0 0 1.285-.3L10 10.413V13h2V9.586zM6 6a1 1 0 1 1 1-1a1 1 0 0 1-1 1m13-1a3 3 0 1 0-4 2.815V13h2V7.816A3 3 0 0 0 19 5m-3 1a1 1 0 1 1 1-1a1 1 0 0 1-1 1m10-4a3.003 3.003 0 0 0-3 3a3 3 0 0 0 .3 1.285l-3.3 3.3V13h2v-2.586L24.715 7.7A2.96 2.96 0 0 0 26 8a3 3 0 0 0 0-6m0 4a1 1 0 1 1 1-1a1 1 0 0 1-1 1M12 19h-2v2.586L7.285 24.3A2.96 2.96 0 0 0 6 24a3 3 0 1 0 3 3a3 3 0 0 0-.3-1.285l3.3-3.3zm-6 9a1 1 0 1 1 1-1a1 1 0 0 1-1 1m11-3.816V19h-2v5.184a3 3 0 1 0 2 0M16 28a1 1 0 1 1 1-1a1 1 0 0 1-1 1m10-4a2.96 2.96 0 0 0-1.285.3L22 21.587V19h-2v3.414l3.3 3.3A3 3 0 0 0 23 27a3 3 0 1 0 3-3m0 4a1 1 0 1 1 1-1a1 1 0 0 1-1 1"/></svg>', Ui = '<svg xmlns="http://www.w3.org/2000/svg" width="30" height="24" viewBox="0 0 640 512"><path fill="currentColor" d="M519.8 62.4c16.8-5.6 25.8-23.7 20.2-40.5S516.3-3.9 499.6 1.6l-113 37.7C372.7 15.8 347 0 317.7 0c-44.2 0-80 35.8-80 80c0 3 .2 5.9.5 8.8l-122.6 40.8c-16.8 5.6-25.8 23.7-20.2 40.5s23.7 25.8 40.5 20.2l135.5-45.2c4.5 3.2 9.3 5.9 14.4 8.2V480c0 17.7 14.3 32 32 32h192c17.7 0 32-14.3 32-32s-14.3-32-32-32h-160V153.3c21-9.2 37.2-27 44.2-49l125.9-42zM437.3 288l72.4-124.2L582.1 288H437.2zm72.4 96c62.9 0 115.2-34 126-78.9c2.6-11-1-22.3-6.7-32.1l-95.2-163.2c-5-8.6-14.2-13.8-24.1-13.8s-19.1 5.3-24.1 13.8l-95.2 163.3c-5.7 9.8-9.3 21.1-6.7 32.1c10.8 44.8 63.1 78.9 126 78.9zm-382.9-92.2L199.2 416H54.3l72.4-124.2zM.9 433.1C11.7 478 64 512 126.8 512s115.2-34 126-78.9c2.6-11-1-22.3-6.7-32.1l-95.2-163.2c-5-8.6-14.2-13.8-24.1-13.8s-19.1 5.3-24.1 13.8L7.6 401.1c-5.7 9.8-9.3 21.1-6.7 32.1z"/></svg>', ji = '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24"><path fill="currentColor" d="m16.957 10.207l2.5-2.5a1 1 0 0 0-1.414-1.414l-.793.793V4a1 1 0 1 0-2 0v3.086l-.793-.793a1 1 0 1 0-1.414 1.414l2.5 2.5a1 1 0 0 0 1.414 0M4 6.5A2.5 2.5 0 0 1 6.5 4h4a1 1 0 1 1 0 2h-4a.5.5 0 0 0-.5.5v11a.5.5 0 0 0 .5.5h4a1 1 0 1 1 0 2h-4A2.5 2.5 0 0 1 4 17.5zm15.457 9.793l-2.5-2.5a1 1 0 0 0-1.414 0l-2.5 2.5a1 1 0 0 0 1.414 1.414l.793-.793V20a1 1 0 1 0 2 0v-3.086l.793.793a1 1 0 0 0 1.414-1.414"/></svg>', Yi = '<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 16 16"><path fill="currentColor" d="m0 15l6-5l-6-4.9zm9-4.9l6 4.9V5zm5 2.8l-3.4-2.8l3.4-3zM7 5h1v1H7zm0-2h1v1H7zm0 4h1v1H7zm0 2h1v1H7zm0 2h1v1H7zm0 2h1v1H7zm0 2h1v1H7z"/><path fill="currentColor" d="M7.5 1c1.3 0 2.6.7 3.6 1.9L10 4h3V1l-1.2 1.2C10.6.8 9.1 0 7.5 0C5.6 0 3.9 1 2.6 2.9l.8.6C4.5 1.9 5.9 1 7.5 1"/></svg>', Xi = '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 36 36"><path fill="currentColor" d="M24.23 11.71a39 39 0 0 0-4.57-3.92a23 23 0 0 1 3.48-1.72c.32-.12.62-.21.92-.3a2.28 2.28 0 0 0 3.81-.46a3.3 3.3 0 0 1 1.92.84c1.19 1.19 1.22 3.59.1 6.58c.49.65.94 1.31 1.35 2c.17-.4.35-.79.49-1.18c1.47-3.85 1.28-7-.53-8.78a5.3 5.3 0 0 0-3.33-1.44a2.29 2.29 0 0 0-4.31.54c-.37.11-.74.22-1.13.37a26 26 0 0 0-4.57 2.35a26 26 0 0 0-4.58-2.39c-3.85-1.46-7-1.28-8.77.53c-1.66 1.67-1.93 4.44-.83 7.86a2.28 2.28 0 0 0 1.59 3.67c.32.61.67 1.22 1.06 1.82A25.5 25.5 0 0 0 4 22.66c-1.47 3.84-1.28 7 .53 8.77a5.63 5.63 0 0 0 4.12 1.51a13.3 13.3 0 0 0 4.65-1a26 26 0 0 0 4.58-2.35A26 26 0 0 0 22.43 32a14.2 14.2 0 0 0 3.65.9a2.3 2.3 0 0 0 4.38-.9a4.6 4.6 0 0 0 .74-.57c1.81-1.81 2-4.93.53-8.77a32.7 32.7 0 0 0-7.5-10.95M12.57 30.09c-3 1.15-5.45 1.13-6.65-.08s-1.23-3.62-.07-6.64a23 23 0 0 1 1.71-3.48a40 40 0 0 0 3.92 4.56c.43.43.87.85 1.31 1.25q.9-.46 1.83-1.05c-.58-.52-1.16-1-1.72-1.61a34 34 0 0 1-5.74-7.47a2.29 2.29 0 0 0-1.66-3.88c-.75-2.5-.62-4.49.43-5.54a3.72 3.72 0 0 1 2.72-.92a11.4 11.4 0 0 1 3.93.84a23 23 0 0 1 3.48 1.72a39 39 0 0 0-4.57 3.92c-.44.44-.87.9-1.29 1.36a20 20 0 0 0 1 1.85c.54-.61 1.09-1.21 1.68-1.8a36.3 36.3 0 0 1 5-4.17a37 37 0 0 1 4.95 4.17a36.3 36.3 0 0 1 4.17 5a37 37 0 0 1-4.17 5a30.7 30.7 0 0 1-10.26 6.97M29.79 30l-.16.13a2.27 2.27 0 0 0-3.5.72a12.6 12.6 0 0 1-3-.77a22 22 0 0 1-3.48-1.72a39 39 0 0 0 4.57-3.92a38 38 0 0 0 3.92-4.56a23 23 0 0 1 1.72 3.48C31 26.39 31 28.81 29.79 30" class="clr-i-solid clr-i-solid-path-1"/><circle cx="17.99" cy="18.07" r="3.3" fill="currentColor" transform="rotate(-9.22 17.955 18.05)"/><path fill="none" d="M0 0h36v36H0z"/></svg>', Ar = '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 36 36"><path d="M25.837 2.03a2.29 2.29 0 0 0-2.276 1.84c-.37.11-.741.22-1.131.37a26 26 0 0 0-4.57 2.349A26 26 0 0 0 13.28 4.2C10.806 3.263 8.62 3 6.905 3.413l1.82 1.82a11.4 11.4 0 0 1 3.855.837 23 23 0 0 1 3.48 1.72 39 39 0 0 0-2.654 2.124l1.41 1.41A36.3 36.3 0 0 1 17.88 8.95a37 37 0 0 1 4.951 4.17 36.3 36.3 0 0 1 4.169 5 37 37 0 0 1-2.353 3.038l1.372 1.368a38 38 0 0 0 2.12-2.645 23 23 0 0 1 1.72 3.48c.545 1.447.83 2.752.847 3.853v.003l1.81 1.807c.42-1.718.162-3.89-.785-6.363a32.7 32.7 0 0 0-7.5-10.951 39 39 0 0 0-4.57-3.92 23 23 0 0 1 3.478-1.72c.32-.12.62-.211.92-.301a2.28 2.28 0 0 0 3.811-.46 3.3 3.3 0 0 1 1.92.84c1.19 1.19 1.219 3.59.099 6.58.49.65.94 1.311 1.35 2.001.17-.4.352-.79.492-1.18 1.47-3.85 1.28-7-.53-8.78a5.3 5.3 0 0 0-3.33-1.439 2.29 2.29 0 0 0-2.034-1.3ZM4.195 5.08C2.82 6.774 2.653 9.397 3.68 12.59a2.28 2.28 0 0 0 1.59 3.67c.32.61.671 1.22 1.061 1.82A25.5 25.5 0 0 0 4 22.661c-1.47 3.84-1.28 6.999.53 8.769a5.63 5.63 0 0 0 4.122 1.511 13.3 13.3 0 0 0 4.65-1.002 26 26 0 0 0 4.579-2.35 26 26 0 0 0 4.55 2.412 14.2 14.2 0 0 0 3.65.9 2.3 2.3 0 0 0 4.38-.9 4.6 4.6 0 0 0 .39-.27l-2.048-2.047a2.27 2.27 0 0 0-2.672 1.166 12.6 12.6 0 0 1-3-.77 22 22 0 0 1-3.48-1.72 39 39 0 0 0 4.236-3.59l-1.35-1.353a30.7 30.7 0 0 1-9.965 6.674c-3 1.15-5.45 1.128-6.65-.082-1.2-1.21-1.23-3.619-.07-6.639a23 23 0 0 1 1.708-3.48 40 40 0 0 0 3.922 4.561c.43.43.87.848 1.31 1.248.6-.306 1.208-.655 1.828-1.049-.58-.52-1.16-1-1.72-1.61A34 34 0 0 1 7.16 15.57 2.29 2.29 0 0 0 5.5 11.69c-.67-2.236-.634-4.061.132-5.173v-.003zm6.967 6.964c-.326.336-.646.68-.96 1.025a20 20 0 0 0 .998 1.852c.442-.499.891-.991 1.363-1.477z" fill="currentColor" /><circle cx="14.866" cy="20.714" r="3.3" fill="currentColor" transform="rotate(-9.22)"/><path fill="none" d="M0 0h36v36H0Z"/><path fill="currentColor" d="m.147 5.402 3.926 3.926L25.645 30.9l5.028 5.027 2.186-2.186L2.334 3.216" style="stroke-width:1.72169"/></svg>', Ts = '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24"><path fill="currentColor" d="M14.76 20.83L17.6 18l-2.84-2.83l1.41-1.41L19 16.57l2.83-2.81l1.41 1.41L20.43 18l2.81 2.83l-1.41 1.41L19 19.4l-2.83 2.84zM12 12v7.88c.04.3-.06.62-.29.83a.996.996 0 0 1-1.41 0L8.29 18.7a.99.99 0 0 1-.29-.83V12h-.03L2.21 4.62a1 1 0 0 1 .17-1.4c.19-.14.4-.22.62-.22h14c.22 0 .43.08.62.22a1 1 0 0 1 .17 1.4L12.03 12z"/></svg>', Ps = '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24"><path fill="currentColor" d="M12 12v7.88c.04.3-.06.62-.29.83a.996.996 0 0 1-1.41 0L8.29 18.7a.99.99 0 0 1-.29-.83V12h-.03L2.21 4.62a1 1 0 0 1 .17-1.4c.19-.14.4-.22.62-.22h14c.22 0 .43.08.62.22a1 1 0 0 1 .17 1.4L12.03 12zm3 5h3v-3h2v3h3v2h-3v3h-2v-3h-3z"/></svg>', Gu = `<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 16 16">
    <path fill="currentColor" d="M5.655 2.639a.5.5 0 0 0 .69.723l1.313-1.254a.5.5 0 0 1 .691.001l1.305 1.252a.5.5 0 0 0 .692-.721L9.042 1.388a1.5 1.5 0 0 0-2.075-.003zM3.362 6.346a.5.5 0 1 0-.723-.69L1.388 6.963a1.5 1.5 0 0 0 0 2.073l1.251 1.31a.5.5 0 0 0 .723-.691l-1.251-1.31a.5.5 0 0 1 0-.69zm2.984 6.293a.5.5 0 0 0-.691.723l1.314 1.256a1.5 1.5 0 0 0 2.077-.004l1.301-1.254a.5.5 0 1 0-.694-.72l-1.3 1.254a.5.5 0 0 1-.693.001zm7.015-6.985a.5.5 0 1 0-.722.693l1.258 1.31a.5.5 0 0 1 0 .693L12.64 9.654a.5.5 0 1 0 .72.694l1.257-1.304a1.5 1.5 0 0 0 .001-2.08zM5 6.5A1.5 1.5 0 0 1 6.5 5h3A1.5 1.5 0 0 1 11 6.5v3A1.5 1.5 0 0 1 9.5 11h-3A1.5 1.5 0 0 1 5 9.5z" />
</svg>`, qu = `<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24">
    <path fill="currentColor" d="M18 10h-4V6a2 2 0 0 0-4 0l.071 4H6a2 2 0 0 0 0 4l4.071-.071L10 18a2 2 0 0 0 4 0v-4.071L18 14a2 2 0 0 0 0-4" />
</svg>`, Vu = `<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 16 16">
    <path fill="currentColor" fill-rule="evenodd" d="M2 8a1 1 0 0 1 1-1h10a1 1 0 0 1 0 2H3a1 1 0 0 1-1-1" clip-rule="evenodd" />
</svg>`, pi = (i) => `<svg xmlns="http://www.w3.org/2000/svg" width="${i ?? 24}" height="${i ?? 24}" viewBox="0 0 24 24" style="filter: drop-shadow(0px 2px 1px #00000033);">
    <g fill="none" stroke="currentColor" stroke-width="1.5">
        <path stroke-linejoin="round" d="M8 6h1.78c2.017 0 3.025 0 3.534.241a2.5 2.5 0 0 1 1.211 3.276c-.229.515-.994 1.17-2.525 2.483c-1.53 1.312-2.296 1.968-2.525 2.483a2.5 2.5 0 0 0 1.211 3.276c.51.241 1.517.241 3.534.241H16" />
        <path d="M2 6a3 3 0 1 0 6 0a3 3 0 0 0-6 0Zm14 12a3 3 0 1 0 6 0a3 3 0 0 0-6 0Z" />
    </g>
</svg>`, Ds = (i) => `<svg xmlns="http://www.w3.org/2000/svg" width="${i}" height="${i}" viewBox="0 0 256 256" ><g fill="currentColor"><path d="M216 40v176H40V40Z" opacity="0.2"/><path d="M152 40a8 8 0 0 1-8 8h-32a8 8 0 0 1 0-16h32a8 8 0 0 1 8 8m-8 168h-32a8 8 0 0 0 0 16h32a8 8 0 0 0 0-16m64-176h-24a8 8 0 0 0 0 16h24v24a8 8 0 0 0 16 0V48a16 16 0 0 0-16-16m8 72a8 8 0 0 0-8 8v32a8 8 0 0 0 16 0v-32a8 8 0 0 0-8-8m0 72a8 8 0 0 0-8 8v24h-24a8 8 0 0 0 0 16h24a16 16 0 0 0 16-16v-24a8 8 0 0 0-8-8M40 152a8 8 0 0 0 8-8v-32a8 8 0 0 0-16 0v32a8 8 0 0 0 8 8m32 56H48v-24a8 8 0 0 0-16 0v24a16 16 0 0 0 16 16h24a8 8 0 0 0 0-16m0-176H48a16 16 0 0 0-16 16v24a8 8 0 0 0 16 0V48h24a8 8 0 0 0 0-16"/></g></svg>`, Uu = '<svg width="16" height="16"viewBox="0 0 3.4393651 3.7032704" version="1.1" id="svg1" xmlns="http://www.w3.org/2000/svg" xmlns:svg="http://www.w3.org/2000/svg"> <defs id="defs1" /> <g id="layer1" transform="translate(-128.32315,-97.896729)" fill="currentColor"> <path id="path1" d="m 130.91707,97.898417 a 0.79375,0.79375 0 0 0 -0.71416,0.999939 l -0.51729,0.296106 a 0.79375,0.79375 0 1 0 0,1.107428 l 0.51729,0.29559 a 0.79454375,0.79454375 0 0 0 0.76584,1.00252 0.79375,0.79375 0 1 0 -0.56896,-1.3472 l -0.51728,-0.296111 a 0.79375,0.79375 0 0 0 0,-0.417545 l 0.51728,-0.296106 a 0.79375,0.79375 0 0 0 1.36271,-0.553455 0.79375,0.79375 0 0 0 -0.84543,-0.791166 z m 0.0517,0.394291 a 0.396875,0.396875 0 0 1 0,0.79375 0.396875,0.396875 0 1 1 0,-0.79375 z m 0,2.116662 a 0.396875,0.396875 0 0 1 0,0.79375 0.396875,0.396875 0 0 1 0,-0.79375 z" /> </g> </svg> ', Fs = `<svg aria-hidden="true" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 20 20">
    <path stroke="currentColor" stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="m19 19-4-4m0-7A7 7 0 1 1 1 8a7 7 0 0 1 14 0Z"/>
</svg>`, zs = `<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 16 16">
    <path fill="currentColor" d="M1.5 1.5A.5.5 0 0 1 2 1h12a.5.5 0 0 1 .5.5v2a.5.5 0 0 1-.128.334L10 8.692V13.5a.5.5 0 0 1-.342.474l-3 1A.5.5 0 0 1 6 14.5V8.692L1.628 3.834A.5.5 0 0 1 1.5 3.5z" />
</svg>`, ju = '<svg xmlns="http://www.w3.org/2000/svg" width="256" height="256" viewBox="0 0 256 256"><path fill="currentColor" d="M227.73 66.85L160 139.17v55.49a16 16 0 0 1-7.13 13.34l-32 21.34A16 16 0 0 1 96 216v-76.83L28.27 66.85l-.08-.09A16 16 0 0 1 40 40h176a16 16 0 0 1 11.84 26.76ZM227.31 192l18.35-18.34a8 8 0 0 0-11.32-11.32L216 180.69l-18.34-18.35a8 8 0 0 0-11.32 11.32L204.69 192l-18.35 18.34a8 8 0 0 0 11.32 11.32L216 203.31l18.34 18.35a8 8 0 0 0 11.32-11.32Z"/></svg>', Yu = `<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 48 48">
    <g fill="none" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round" stroke-width="4">
        <path d="M11.272 36.728A17.94 17.94 0 0 0 24 42c9.941 0 18-8.059 18-18S33.941 6 24 6c-4.97 0-9.47 2.015-12.728 5.272C9.614 12.93 6 17 6 17" />
        <path d="M6 9v8h8" />
    </g>
</svg>`, Xu = `<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 48 48" style="transform: scaleX(-1); transform-origin: center;">
    <g fill="none" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round" stroke-width="4">
        <path d="M11.272 36.728A17.94 17.94 0 0 0 24 42c9.941 0 18-8.059 18-18S33.941 6 24 6c-4.97 0-9.47 2.015-12.728 5.272C9.614 12.93 6 17 6 17" />
        <path d="M6 9v8h8" />
    </g>
</svg>`, Wu = '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24"><path fill="currentColor" d="M13 20h-2V8l-5.5 5.5l-1.42-1.42L12 4.16l7.92 7.92l-1.42 1.42L13 8z"/></svg>', Ku = '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24"><path fill="currentColor" d="M11 4h2v12l5.5-5.5l1.42 1.42L12 19.84l-7.92-7.92L5.5 10.5L11 16z"/></svg>', Zu = '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24"><path fill="none" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 12h14M5 12l4-4m-4 4l4 4"/></svg>', Qu = '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24"><path fill="none" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 12H5m14 0l-4 4m4-4l-4-4"/></svg>', Ju = '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24"><path fill="none" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M19.75 5.623V9.52a4 4 0 0 1-4 4H3.871m4.236 4.857L4.31 14.58a1.5 1.5 0 0 1-.44-1.061m4.236-4.857L4.31 12.46c-.293.293-.44.677-.44 1.061"/></svg>', le = '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24"><path fill="currentColor" d="m15.113 3.21l.094.083l5.5 5.5a1 1 0 0 1-1.175 1.59l-3.172 3.171l-1.424 3.797a1 1 0 0 1-.158.277l-.07.08l-1.5 1.5a1 1 0 0 1-1.32.082l-.095-.083L9 16.415l-3.793 3.792a1 1 0 0 1-1.497-1.32l.083-.094L7.585 15l-2.792-2.793a1 1 0 0 1-.083-1.32l.083-.094l1.5-1.5a1 1 0 0 1 .258-.187l.098-.042l3.796-1.425l3.171-3.17a1 1 0 0 1 1.497-1.26z"/></svg>', Pn = '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24"><path fill="currentColor" d="m20.971 17.172l-1.414 1.414l-3.535-3.535l-.073.074l-.707 3.535l-1.415 1.415l-4.242-4.243l-4.95 4.95l-1.414-1.414l4.95-4.95l-4.243-4.243l1.414-1.414l3.536-.707l.073-.074l-3.536-3.536l1.414-1.415zm-2.12-4.95l1.34-1.34l.707.707l1.415-1.414l-8.486-8.485l-1.414 1.414l.707.707l-1.34 1.34z"/></svg>', tp = '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24"><path fill="none" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="m7 7l10 10M7 17L17 7"/></svg>', Bs = '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 48 48"><defs><mask id="SVGhUb5Xdyy"><g fill="none"><path stroke="#fff" stroke-linecap="round" stroke-linejoin="round" stroke-width="4" d="M16 6H8a2 2 0 0 0-2 2v8m10 26H8a2 2 0 0 1-2-2v-8m26 10h8a2 2 0 0 0 2-2v-8M32 6h8a2 2 0 0 1 2 2v8"/><rect width="20" height="20" x="14" y="14" fill="#fff" stroke="#fff" stroke-width="4" rx="10"/><circle r="3" fill="#000" transform="matrix(-1 0 0 1 24 24)"/></g></mask></defs><path fill="currentColor" d="M0 0h48v48H0z" mask="url(#SVGhUb5Xdyy)"/></svg>', ep = '<svg xmlns="http://www.w3.org/2000/svg" width="${fixedPreviewSize}" height="${fixedPreviewSize}" viewBox="0 0 256 256" ><g fill="currentColor"><path d="M216 40v176H40V40Z" opacity="0.2"/><path d="M152 40a8 8 0 0 1-8 8h-32a8 8 0 0 1 0-16h32a8 8 0 0 1 8 8m-8 168h-32a8 8 0 0 0 0 16h32a8 8 0 0 0 0-16m64-176h-24a8 8 0 0 0 0 16h24v24a8 8 0 0 0 16 0V48a16 16 0 0 0-16-16m8 72a8 8 0 0 0-8 8v32a8 8 0 0 0 16 0v-32a8 8 0 0 0-8-8m0 72a8 8 0 0 0-8 8v24h-24a8 8 0 0 0 0 16h24a16 16 0 0 0 16-16v-24a8 8 0 0 0-8-8M40 152a8 8 0 0 0 8-8v-32a8 8 0 0 0-16 0v32a8 8 0 0 0 8 8m32 56H48v-24a8 8 0 0 0-16 0v24a16 16 0 0 0 16 16h24a8 8 0 0 0 0-16m0-176H48a16 16 0 0 0-16 16v24a8 8 0 0 0 16 0V48h24a8 8 0 0 0 0-16"/></g></svg>', vn = '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24"><path fill="currentColor" d="M11.83 9L15 12.16V12a3 3 0 0 0-3-3zm-4.3.8l1.55 1.55c-.05.21-.08.42-.08.65a3 3 0 0 0 3 3c.22 0 .44-.03.65-.08l1.55 1.55c-.67.33-1.41.53-2.2.53a5 5 0 0 1-5-5c0-.79.2-1.53.53-2.2M2 4.27l2.28 2.28l.45.45C3.08 8.3 1.78 10 1 12c1.73 4.39 6 7.5 11 7.5c1.55 0 3.03-.3 4.38-.84l.43.42L19.73 22L21 20.73L3.27 3M12 7a5 5 0 0 1 5 5c0 .64-.13 1.26-.36 1.82l2.93 2.93c1.5-1.25 2.7-2.89 3.43-4.75c-1.73-4.39-6-7.5-11-7.5c-1.4 0-2.74.25-4 .7l2.17 2.15C10.74 7.13 11.35 7 12 7"/></svg>', Ir = '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24"><path fill="currentColor" d="M12 9a3 3 0 0 0-3 3a3 3 0 0 0 3 3a3 3 0 0 0 3-3a3 3 0 0 0-3-3m0 8a5 5 0 0 1-5-5a5 5 0 0 1 5-5a5 5 0 0 1 5 5a5 5 0 0 1-5 5m0-12.5C7 4.5 2.73 7.61 1 12c1.73 4.39 6 7.5 11 7.5s9.27-3.11 11-7.5c-1.73-4.39-6-7.5-11-7.5"/></svg>', Rs = '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 32 32"><circle cx="21" cy="26" r="2" fill="currentColor"/><circle cx="21" cy="6" r="2" fill="currentColor"/><circle cx="4" cy="16" r="2" fill="currentColor"/><path fill="currentColor" d="M28 12a3.996 3.996 0 0 0-3.858 3h-4.284a3.966 3.966 0 0 0-5.491-2.643l-3.177-3.97A3.96 3.96 0 0 0 12 6a4 4 0 1 0-4 4a4 4 0 0 0 1.634-.357l3.176 3.97a3.924 3.924 0 0 0 0 4.774l-3.176 3.97A4 4 0 0 0 8 22a4 4 0 1 0 4 4a3.96 3.96 0 0 0-.81-2.387l3.176-3.97A3.966 3.966 0 0 0 19.858 17h4.284A3.993 3.993 0 1 0 28 12M6 6a2 2 0 1 1 2 2a2 2 0 0 1-2-2m2 22a2 2 0 1 1 2-2a2 2 0 0 1-2 2m8-10a2 2 0 1 1 2-2a2 2 0 0 1-2 2m12 0a2 2 0 1 1 2-2a2 2 0 0 1-2 2"/></svg>', ip = '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24"><g fill="none" stroke="currentColor" stroke-linejoin="round" stroke-width="1.5"><path stroke-linecap="round" d="M17.5 17.5L22 22"/><path d="M20 11a9 9 0 1 0-18 0a9 9 0 0 0 18 0Z"/><path stroke-linecap="round" d="m14.5 9.5l.92.793c.387.333.58.5.58.707s-.193.374-.58.707l-.92.793m-7-3l-.92.793c-.387.333-.58.5-.58.707s.193.374.58.707l.92.793m4.5-4l-2 5"/></g></svg>', np = '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24"><path fill="currentColor" fill-rule="evenodd" d="M20 4H4a1 1 0 0 0-1 1v14a1 1 0 0 0 1 1h16a1 1 0 0 0 1-1V5a1 1 0 0 0-1-1M4 2a3 3 0 0 0-3 3v14a3 3 0 0 0 3 3h16a3 3 0 0 0 3-3V5a3 3 0 0 0-3-3zm2 5h2v2H6zm5 0a1 1 0 1 0 0 2h6a1 1 0 1 0 0-2zm-3 4H6v2h2zm2 1a1 1 0 0 1 1-1h6a1 1 0 1 1 0 2h-6a1 1 0 0 1-1-1m-2 3H6v2h2zm2 1a1 1 0 0 1 1-1h6a1 1 0 1 1 0 2h-6a1 1 0 0 1-1-1" clip-rule="evenodd"/></svg>', rp = '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24"><path fill="currentColor" d="m11.852 2.011l.058-.007L12 2l.075.003l.126.017l.111.03l.111.044l.098.052l.104.074l.082.073l3 3a1 1 0 1 1-1.414 1.414L13 5.415V13a1 1 0 0 1-2 0V5.415L9.707 6.707a1 1 0 0 1-1.32.083l-.094-.083a1 1 0 0 1 0-1.414l3-3q.053-.054.112-.097l.11-.071l.114-.054l.105-.035zM12 16a3 3 0 1 1 0 6a3 3 0 0 1 0-6"/></svg>', sp = '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24"><path fill="currentColor" d="M12 10a1 1 0 0 1 1 1v7.584l1.293-1.291a1 1 0 0 1 1.32-.083l.094.083a1 1 0 0 1 0 1.414l-3 3a1 1 0 0 1-.112.097l-.11.071l-.114.054l-.105.035l-.149.03L12 22l-.075-.003l-.126-.017l-.111-.03l-.111-.044l-.098-.052l-.096-.067l-.09-.08l-3-3a1 1 0 0 1 1.414-1.414L11 18.586V11a1 1 0 0 1 1-1m0-8a3 3 0 1 1-3 3l.005-.176A3 3 0 0 1 12 2"/></svg>';
function se(i, t) {
  if (Array.isArray(i) && Array.isArray(t))
    return [...i, ...t];
  if (typeof i == "object" && typeof t == "object" && i && t) {
    const e = { ...i };
    for (const n in t)
      Object.prototype.hasOwnProperty.call(t, n) && (n in i ? e[n] = se(i[n], t[n]) : e[n] = t[n]);
    return e;
  }
  return t;
}
const op = {
  topbar: [
    {
      title: "Pin Nodes",
      svgIcon: le,
      variant: "outline-primary",
      visible: !0,
      onclick(i, t) {
        t.forEach((e) => {
          e.freeze();
        });
      }
    },
    {
      title: "Unpin Node",
      svgIcon: Pn,
      variant: "outline-primary",
      visible: !0,
      onclick(i, t) {
        t.forEach((e) => {
          e.unfreeze(), this.uiManager.graph.simulation.reheat();
        });
      }
    },
    {
      title: "Hide Nodes",
      svgIcon: vn,
      variant: "outline-danger",
      visible: !0,
      flushRight: !0,
      onclick(i, t) {
        t.forEach((e) => {
          this.uiManager.graph.queryEngine.excludeNode(e), this.uiManager.graph.renderer.getGraphInteraction().unselectAll();
        });
      }
    }
  ],
  menu: [
    {
      text: "Expand Nodes",
      title: "Expand Node",
      svgIcon: Rs,
      variant: "outline-primary",
      visible: !1
    },
    {
      text: "Pin Nodes",
      title: "Pin Nodes",
      svgIcon: le,
      variant: "outline-primary",
      visible: !0,
      onclick(i, t) {
        t.forEach((e) => {
          e.freeze();
        });
      }
    }
  ]
};
class ap {
  constructor(t) {
    f(this, "uiManager");
    f(this, "navigation");
    f(this, "selectionMenu");
    f(this, "layoutMenu");
    f(this, "selectionMenuShown", !1);
    f(this, "menuNode");
    f(this, "layoutTypeOptions", [
      {
        root: {
          id: "pvt-graphcontrols-simulation-toggle",
          class: "",
          title: "Toggle graph physic simulation",
          svgIcon: Xi,
          onClick: () => {
            this.togglePhysicSimulation();
          }
        },
        children: [
          {
            id: "pvt-graphcontrols-simulation-stop",
            class: "",
            title: "Stop graph physic simulation",
            svgIcon: Ar,
            onClick: () => {
              this.togglePhysicSimulation(!1);
            }
          },
          {
            id: "pvt-graphcontrols-simulation-start",
            class: "",
            title: "Start graph physic simulation",
            svgIcon: Xi,
            onClick: () => {
              this.togglePhysicSimulation(!0);
            }
          }
        ]
      },
      {
        root: {
          id: "pvt-graphcontrols-layout-organic",
          class: "",
          title: "Change Graph Layout to Organic",
          svgIcon: Du,
          onClick: () => {
            this.uiManager.graph.simulation.changeLayout("force");
          }
        },
        children: [
          {
            id: "pvt-graphcontrols-layout-organic-5",
            class: "",
            title: "Run Organic Layout for 5 seconds. Or until it stabilises",
            svgIcon: Ru,
            onClick: () => {
              this.uiManager.graph.simulation.changeLayout("force", { cooldownTime: 5e3 });
            }
          },
          {
            id: "pvt-graphcontrols-layout-organic-10",
            class: "",
            title: "Run Organic Layout for 10 seconds. Or until it stabilises",
            svgIcon: Hu,
            onClick: () => {
              this.uiManager.graph.simulation.changeLayout("force", { cooldownTime: 1e4 });
            }
          },
          {
            id: "pvt-graphcontrols-layout-organic-15",
            class: "",
            title: "Run Organic Layout for 15 seconds. Or until it stabilises",
            svgIcon: $u,
            onClick: () => {
              this.uiManager.graph.simulation.changeLayout("force", { cooldownTime: 15e3 });
            }
          }
        ]
      },
      {
        root: {
          id: "pvt-graphcontrols-layout-tree-v",
          class: "pvt-graphcontrols-layout-tree-v-options",
          title: "Change Graph Layout to Vertical Tree",
          svgIcon: Fu,
          onClick: () => {
            this.uiManager.graph.simulation.changeLayout("tree", { layout: { horizontal: !1 } });
          }
        },
        children: [
          {
            id: "pvt-graphcontrols-layout-tree-v-FirstZeroInDegree",
            class: "pvt-graphcontrols-layout-tree-v-options",
            title: "Pick the first valid 0 in-degree node",
            svgIcon: qi,
            onClick: () => {
              this.uiManager.graph.simulation.changeLayout("tree", { layout: { horizontal: !1, rootIdAlgorithmFinder: "FirstZeroInDegree" } });
            }
          },
          {
            id: "pvt-graphcontrols-layout-tree-v-MaxReachability",
            class: "pvt-graphcontrols-layout-tree-v-options",
            title: "Pick the most connected node based on the reachability to others",
            svgIcon: Vi,
            onClick: () => {
              this.uiManager.graph.simulation.changeLayout("tree", { layout: { horizontal: !1, rootIdAlgorithmFinder: "MaxReachability" } });
            }
          },
          {
            id: "pvt-graphcontrols-layout-tree-v-MinMaxDistance",
            class: "pvt-graphcontrols-layout-tree-v-options",
            title: "Minimize max distance by trying to balance subtree",
            svgIcon: Ui,
            onClick: () => {
              this.uiManager.graph.simulation.changeLayout("tree", { layout: { horizontal: !1, rootIdAlgorithmFinder: "MinMaxDistance" } });
            }
          },
          {
            id: "pvt-graphcontrols-layout-tree-v-MinHeight",
            class: "pvt-graphcontrols-layout-tree-v-options",
            title: "Pick node minimizing tree height",
            svgIcon: ji,
            onClick: () => {
              this.uiManager.graph.simulation.changeLayout("tree", { layout: { horizontal: !1, rootIdAlgorithmFinder: "MinHeight" } });
            }
          },
          {
            id: "pvt-graphcontrols-layout-tree-v-FlipEdgeDirection",
            class: "pvt-graphcontrols-layout-tree-v-options",
            title: "Flip the direction of all edges, then pick the most connected node based on the reachability to others",
            svgIcon: Yi,
            onClick: () => {
              this.uiManager.graph.simulation.changeLayout("tree", { layout: { horizontal: !1, rootIdAlgorithmFinder: "MaxReachability", flipEdgeDirection: !0 } });
            }
          }
        ]
      },
      {
        root: {
          id: "pvt-graphcontrols-layout-tree-h",
          class: "pvt-graphcontrols-layout-tree-h-options",
          title: "Change Graph Layout to Horizontal Tree",
          svgIcon: zu,
          onClick: () => {
            this.uiManager.graph.simulation.changeLayout("tree", { layout: { horizontal: !0 } });
          }
        },
        children: [
          {
            id: "pvt-graphcontrols-layout-tree-h-FirstZeroInDegree",
            class: "pvt-graphcontrols-layout-tree-h-options",
            title: "Pick the first valid 0 in-degree node",
            svgIcon: qi,
            onClick: () => {
              this.uiManager.graph.simulation.changeLayout("tree", { layout: { horizontal: !0, rootIdAlgorithmFinder: "FirstZeroInDegree" } });
            }
          },
          {
            id: "pvt-graphcontrols-layout-tree-h-MaxReachability",
            class: "pvt-graphcontrols-layout-tree-h-options",
            title: "Pick the most connected node based on the reachability to others",
            svgIcon: Vi,
            onClick: () => {
              this.uiManager.graph.simulation.changeLayout("tree", { layout: { horizontal: !0, rootIdAlgorithmFinder: "MaxReachability" } });
            }
          },
          {
            id: "pvt-graphcontrols-layout-tree-h-MinMaxDistance",
            class: "pvt-graphcontrols-layout-tree-h-options",
            title: "Minimize max distance by trying to balance subtree",
            svgIcon: Ui,
            onClick: () => {
              this.uiManager.graph.simulation.changeLayout("tree", { layout: { horizontal: !0, rootIdAlgorithmFinder: "MinMaxDistance" } });
            }
          },
          {
            id: "pvt-graphcontrols-layout-tree-h-MinHeight",
            class: "pvt-graphcontrols-layout-tree-h-options",
            title: "Pick node minimizing tree height",
            svgIcon: ji,
            onClick: () => {
              this.uiManager.graph.simulation.changeLayout("tree", { layout: { horizontal: !0, rootIdAlgorithmFinder: "MinHeight" } });
            }
          },
          {
            id: "pvt-graphcontrols-layout-tree-h-FlipEdgeDirection",
            class: "pvt-graphcontrols-layout-tree-h-options",
            title: "Flip the direction of all edges, then pick the most connected node based on the reachability to others",
            svgIcon: Yi,
            onClick: () => {
              this.uiManager.graph.simulation.changeLayout("tree", { layout: { horizontal: !0, rootIdAlgorithmFinder: "MaxReachability", flipEdgeDirection: !0 } });
            }
          }
        ]
      },
      {
        root: {
          id: "pvt-graphcontrols-layout-tree-r",
          class: "pvt-graphcontrols-layout-tree-r-options",
          title: "Change Graph Layout to Radial Tree",
          svgIcon: Bu,
          onClick: () => {
            this.uiManager.graph.simulation.changeLayout("tree", { layout: { radial: !0 } });
          }
        },
        children: [
          {
            id: "pvt-graphcontrols-layout-tree-r-FirstZeroInDegree",
            class: "pvt-graphcontrols-layout-tree-r-options",
            title: "Pick the first valid 0 in-degree node",
            svgIcon: qi,
            onClick: () => {
              this.uiManager.graph.simulation.changeLayout("tree", { layout: { radial: !0, rootIdAlgorithmFinder: "FirstZeroInDegree" } });
            }
          },
          {
            id: "pvt-graphcontrols-layout-tree-r-MaxReachability",
            class: "pvt-graphcontrols-layout-tree-r-options",
            title: "Pick the most connected node based on the reachability to others",
            svgIcon: Vi,
            onClick: () => {
              this.uiManager.graph.simulation.changeLayout("tree", { layout: { radial: !0, rootIdAlgorithmFinder: "MaxReachability" } });
            }
          },
          {
            id: "pvt-graphcontrols-layout-tree-r-MinMaxDistance",
            class: "pvt-graphcontrols-layout-tree-r-options",
            title: "Minimize max distance by trying to balance subtree",
            svgIcon: Ui,
            onClick: () => {
              this.uiManager.graph.simulation.changeLayout("tree", { layout: { radial: !0, rootIdAlgorithmFinder: "MinMaxDistance" } });
            }
          },
          {
            id: "pvt-graphcontrols-layout-tree-r-MinHeight",
            class: "pvt-graphcontrols-layout-tree-r-options",
            title: "Pick node minimizing tree height",
            svgIcon: ji,
            onClick: () => {
              this.uiManager.graph.simulation.changeLayout("tree", { layout: { radial: !0, rootIdAlgorithmFinder: "MinHeight" } });
            }
          },
          {
            id: "pvt-graphcontrols-layout-tree-r-FlipEdgeDirection",
            class: "pvt-graphcontrols-layout-tree-r-options",
            title: "Flip the direction of all edges, then pick the most connected node based on the reachability to others",
            svgIcon: Yi,
            onClick: () => {
              this.uiManager.graph.simulation.changeLayout("tree", { layout: { radial: !0, rootIdAlgorithmFinder: "MaxReachability", flipEdgeDirection: !0 } });
            }
          }
        ]
      }
    ]);
    this.uiManager = t, this.menuNode = se(op, this.uiManager.getOptions().selectionMenu.menuNode ?? {});
  }
  mount(t) {
    if (!t) return;
    const e = document.createElement("template");
    e.innerHTML = `
  <div class="pvt-graphcontrols-elements">
    <div class="pvt-graphcontrols-panel pvt-graphcontrols-layout"></div>
    <div class="pvt-graphcontrols-panel pvt-graphcontrols-selection">
        <div class="pvt-graphcontrols-selection-title"></div>
        <div class="pvt-graphcontrols-selection-topbar"></div>
        <div class="pvt-graphcontrols-selection-mainmenu"></div>
    </div>
  </div>
`, this.navigation = e.content.firstElementChild, t.appendChild(this.navigation);
  }
  destroy() {
    var t;
    (t = this.navigation) == null || t.remove(), this.navigation = void 0;
  }
  afterMount() {
    this.navigation && (this.selectionMenu = this.navigation.querySelector(".pvt-graphcontrols-selection"), this.layoutMenu = this.navigation.querySelector(".pvt-graphcontrols-layout"), this.createLayoutOptionAndBind(this.layoutTypeOptions));
  }
  graphReady() {
    if (!this.navigation) return;
    const t = this.uiManager.graph.getNodes(), e = this.uiManager.graph.getEdges();
    we(t, e) ? (this.navigation.querySelectorAll(".pvt-graphcontrols-layout-tree-v-options").forEach((n) => {
      n.setAttribute("disabled", "disabled"), n.setAttribute("data-old-title", n.getAttribute("title") ?? ""), n.setAttribute("title", "The graph contains a cycle, so it cannot be displayed as a tree.");
    }), this.navigation.querySelectorAll(".pvt-graphcontrols-layout-tree-h-options").forEach((n) => {
      n.setAttribute("disabled", "disabled"), n.setAttribute("data-old-title", n.getAttribute("title") ?? ""), n.setAttribute("title", "The graph contains a cycle, so it cannot be displayed as a tree.");
    }), this.navigation.querySelectorAll(".pvt-graphcontrols-layout-tree-r-options").forEach((n) => {
      n.setAttribute("disabled", "disabled"), n.setAttribute("data-old-title", n.getAttribute("title") ?? ""), n.setAttribute("title", "The graph contains a cycle, so it cannot be displayed as a tree.");
    })) : (this.navigation.querySelectorAll(".pvt-graphcontrols-layout-tree-v-options").forEach((n) => {
      n.removeAttribute("disabled"), n.setAttribute("title", n.getAttribute("data-old-title") ?? "");
    }), this.navigation.querySelectorAll(".pvt-graphcontrols-layout-tree-h-options").forEach((n) => {
      n.removeAttribute("disabled"), n.setAttribute("title", n.getAttribute("data-old-title") ?? "");
    }), this.navigation.querySelectorAll(".pvt-graphcontrols-layout-tree-r-options").forEach((n) => {
      n.removeAttribute("disabled"), n.setAttribute("title", n.getAttribute("data-old-title") ?? "");
    })), this.uiManager.graph.renderer.getGraphInteraction().on("selectNodes", (n) => {
      this.populateNodeSelectionContainer(n), this.showSelectionMenu();
    }), this.uiManager.graph.renderer.getGraphInteraction().on("unselectNodes", () => {
      this.hideSelectionMenu(), setTimeout(this.clearSelectionContainer, 200);
    });
  }
  showSelectionMenu() {
    this.selectionMenuShown || this.selectionMenu && (this.selectionMenu.classList.add("shown"), this.selectionMenuShown = !0);
  }
  hideSelectionMenu() {
    this.selectionMenuShown && this.selectionMenu && (this.selectionMenu.classList.remove("shown"), this.selectionMenuShown = !1);
  }
  populateNodeSelectionContainer(t) {
    if (!this.navigation || !this.selectionMenu) return;
    const e = this.selectionMenu.querySelector(".pvt-graphcontrols-selection-title"), n = this.selectionMenu.querySelector(".pvt-graphcontrols-selection-topbar"), r = this.selectionMenu.querySelector(".pvt-graphcontrols-selection-mainmenu"), s = this.getNodesFromSelection(t);
    e.innerHTML = "", n.innerHTML = "", r.innerHTML = "", e.textContent = `${s.length} nodes selected`, n.appendChild(We(this, this.menuNode.topbar, s)), r.appendChild(Ke(this, this.menuNode.menu, s));
  }
  clearSelectionContainer() {
    if (!this.navigation || !this.selectionMenu) return;
    const t = this.selectionMenu.querySelector(".pvt-graphcontrols-selection-title"), e = this.selectionMenu.querySelector(".pvt-graphcontrols-selection-topbar"), n = this.selectionMenu.querySelector(".pvt-graphcontrols-selection-mainmenu");
    t.innerHTML = "", e.innerHTML = "", n.innerHTML = "";
  }
  getNodesFromSelection(t) {
    return t.map((e) => {
      const { node: n } = e;
      return n;
    });
  }
  createLayoutOptionAndBind(t) {
    t.forEach((e, n) => {
      if (!this.layoutMenu) return;
      n > 0 && this.layoutMenu.appendChild(T("div", {
        class: "pivotick-divider"
      }, []));
      const r = e.root, s = e.children, o = T("div", {}, [
        this.createLayoutOption(r)
      ]), a = this.createLayoutOptionMenu(s), c = T("div", {
        class: "pvt-graphcontrols-layout-type-container"
      }, [
        o,
        a
      ]);
      this.layoutMenu.appendChild(c);
      const l = c.querySelector(`#${r.id}`);
      l && typeof r.onClick == "function" && l.addEventListener("click", r.onClick), s.forEach((h) => {
        const d = a.querySelector(`#${h.id}`);
        d && typeof h.onClick == "function" && d.addEventListener("click", h.onClick);
      });
    });
  }
  createLayoutOptionMenu(t) {
    const e = T("div", {
      class: ["pvt-graphcontrols-layout-type-options"]
    });
    return t.forEach((n) => {
      const r = this.createLayoutOption(n);
      e.appendChild(r);
    }), e;
  }
  createLayoutOption(t) {
    return T("button", {
      id: t.id,
      class: t.class,
      title: t.title
    }, [
      t.html ? t.html() : Y({ svgIcon: t.svgIcon })
    ]);
  }
  togglePhysicSimulation(t) {
    const e = this.uiManager.graph.simulation;
    if (!e) return;
    t ?? !e.isEnabled() ? (e.enable(), this.updatePhysicSimulationIndicator(!0)) : (this.updatePhysicSimulationIndicator(!1), e.disable());
  }
  updatePhysicSimulationIndicator(t) {
    const e = this.layoutMenu.querySelector("#pvt-graphcontrols-simulation-toggle"), n = e.querySelector(".pvt-icon");
    !e || !n || (t ? n.outerHTML = Y({ svgIcon: Xi }).outerHTML : n.outerHTML = Y({ svgIcon: Ar }).outerHTML);
  }
}
class lp {
  constructor(t) {
    f(this, "uiManager");
    f(this, "navigation");
    this.uiManager = t;
  }
  mount(t) {
    if (!t) return;
    const e = document.createElement("template");
    e.innerHTML = `
  <div class="pvt-graphnavigation-elements">
    <div class="pvt-graphnavigation-zoom-fit">
        <button id="pvt-graphnavigation-reset" class="pvt-graphnavigation-reset-button" title="Fit and center">
            ${Gu}
        </button>
    </div>
    <div class="pvt-graphnavigation-zoom-controls">
        <button id="pvt-graphnavigation-zoom-in" class="pvt-graphnavigation-zoomin-button" title="Zoom In">
           ${qu}
        </button>
        <div class="pvt-zoom-divider"></div>
        <button id="pvt-graphnavigation-zoom-out" class="pvt-graphnavigation-zoomout-button" title="Zoom Out">
            ${Vu}
        </button>
    </div>
  </div>
`, this.navigation = e.content.firstElementChild, t.appendChild(this.navigation);
  }
  destroy() {
    var t;
    (t = this.navigation) == null || t.remove(), this.navigation = void 0;
  }
  afterMount() {
    if (!this.navigation) return;
    const t = this.navigation.querySelector("#pvt-graphnavigation-zoom-in"), e = this.navigation.querySelector("#pvt-graphnavigation-zoom-out"), n = this.navigation.querySelector("#pvt-graphnavigation-reset");
    t == null || t.addEventListener("click", () => {
      this.uiManager.graph.renderer.zoomIn();
    }), e == null || e.addEventListener("click", () => {
      this.uiManager.graph.renderer.zoomOut();
    }), n == null || n.addEventListener("click", () => {
      this.uiManager.graph.renderer.fitAndCenter();
    });
  }
  graphReady() {
  }
}
class cp {
  constructor() {
    f(this, "layout");
    f(this, "canvas");
    f(this, "sidebar");
    f(this, "toolbar");
    f(this, "notification");
    f(this, "modal");
    f(this, "slidePanel");
    f(this, "graphnavigation");
    f(this, "graphcontrols");
  }
  mount(t, e = "full") {
    this.layout = document.createElement("div"), this.layout.className = `pvt-layout mode-${e}`, this.canvas = document.createElement("div"), this.canvas.className = "pvt-canvas", this.layout.appendChild(this.canvas), this.notification = document.createElement("div"), this.notification.className = "pvt-notification", this.canvas.appendChild(this.notification), e === "full" && (this.sidebar = document.createElement("div"), this.sidebar.className = "pvt-sidebar", this.layout.appendChild(this.sidebar)), (e === "light" || e === "full") && (this.toolbar = document.createElement("div"), this.toolbar.className = "pvt-toolbar", this.layout.appendChild(this.toolbar), this.modal = document.createElement("div"), this.modal.className = "pvt-modalcontainer", t.appendChild(this.modal), this.slidePanel = document.createElement("div"), this.slidePanel.className = "pvt-slidepanel-container", this.canvas.appendChild(this.slidePanel)), e !== "static" && (this.graphnavigation = document.createElement("div"), this.graphnavigation.className = "pvt-graphnavigation", this.canvas.appendChild(this.graphnavigation), this.graphcontrols = document.createElement("div"), this.graphcontrols.className = "pvt-graphcontrols", this.canvas.appendChild(this.graphcontrols)), t.appendChild(this.layout);
  }
  destroy() {
    var t;
    (t = this.layout) == null || t.remove(), this.layout = void 0;
  }
  afterMount() {
  }
  graphReady() {
  }
}
class hp {
  constructor(t) {
    f(this, "uiManager");
    f(this, "panel");
    f(this, "renderCb");
    this.uiManager = t, this.renderCb = typeof this.uiManager.getOptions().mainHeader.render == "function" ? this.uiManager.getOptions().mainHeader.render : void 0;
  }
  mount(t) {
    t && (this.panel = t);
  }
  destroy() {
    var t;
    (t = this.panel) == null || t.remove(), this.panel = void 0;
  }
  afterMount() {
    this.clearOverview();
  }
  graphReady() {
    this.clearOverview();
  }
  renderCustomContent(t) {
    var n;
    if (!this.panel || !this.renderCb) return;
    this.panel.innerHTML = "";
    const e = St(this.renderCb, t);
    e && ((n = this.panel) == null || n.appendChild(e));
  }
  clearOverview() {
    if (this.panel) {
      if (this.renderCb) {
        this.renderCustomContent(null);
        return;
      }
      this.panel.innerHTML = "", this.showTotalNodeCount();
    }
  }
  /* Single selection */
  updateNodeOverview(t, e) {
    if (!this.panel) return;
    if (this.renderCb) {
      this.renderCustomContent(t);
      return;
    }
    this.panel.innerHTML = "";
    const n = 42, r = `
<div class="enter-ready">
    <div class="pvt-mainheader-nodepreview">
        <svg class="pvt-mainheader-icon" width="${n}" height="${n}" viewBox="0 0 ${n} ${n}" preserveAspectRatio="xMidYMid meet"></svg>
    </div>
    <div class="pvt-mainheader-nodeinfo">
        <div class="pvt-mainheader-nodeinfo-name"></div>
        <div class="pvt-mainheader-nodeinfo-subtitle"></div>
    </div>
    <div class="pvt-mainheader-nodeinfo-action">
    </div>
</div>`, s = ot(r), o = s.querySelector(".pvt-mainheader-icon"), a = s.querySelector(".pvt-mainheader-nodeinfo-name"), c = s.querySelector(".pvt-mainheader-nodeinfo-subtitle");
    if (o && e && e instanceof SVGGElement) {
      const l = e.cloneNode(!0), h = e.getBBox(), d = n / Math.max(h.width, h.height);
      l.setAttribute(
        "transform",
        `translate(${(n - h.width * d) / 2 - h.x * d}, ${(n - h.height * d) / 2 - h.y * d}) scale(${d})`
      ), o.appendChild(l);
    }
    if (a && (a.textContent = Wt(t, this.uiManager.getOptions().mainHeader)), c) {
      const l = As(t, this.uiManager.getOptions().mainHeader);
      c.textContent = l ?? "";
    }
    this.panel.appendChild(s), requestAnimationFrame(() => {
      var l, h;
      (h = (l = this.panel) == null ? void 0 : l.firstElementChild) == null || h.classList.add("enter-active");
    });
  }
  updateEdgeOverview(t) {
    if (!this.panel) return;
    if (this.renderCb) {
      this.renderCustomContent(t);
      return;
    }
    this.panel.innerHTML = "";
    const n = `<div class="enter-ready">
<div class="pvt-mainheader-nodepreview">
    ${pi(42)}
</div>
<div class="pvt-mainheader-nodeinfo">
    <div class="pvt-mainheader-nodeinfo-name"></div>
    <div class="pvt-mainheader-nodeinfo-subtitle"></div>
</div>
<div class="pvt-mainheader-nodeinfo-action">
</div>
</div>`, r = ot(n), s = r.querySelector(".pvt-mainheader-nodeinfo-name"), o = r.querySelector(".pvt-mainheader-nodeinfo-subtitle");
    s && (s.textContent = be(t, this.uiManager.getOptions().mainHeader)), o && (o.textContent = Is(t, this.uiManager.getOptions().mainHeader)), this.panel.appendChild(r), requestAnimationFrame(() => {
      var a, c;
      (c = (a = this.panel) == null ? void 0 : a.firstElementChild) == null || c.classList.add("enter-active");
    });
  }
  /* Multi selection */
  updateNodesOverview(t) {
    if (!this.panel) return;
    if (this.renderCb) {
      this.renderCustomContent(t.map((c) => c.node));
      return;
    }
    this.panel.innerHTML = "";
    const e = 42, n = `<div class="enter-ready">
    <div class="pvt-mainheader-nodepreview">
        <svg class="pvt-mainheader-icon" width="${e}" height="${e}" viewBox="0 0 ${e} ${e}" preserveAspectRatio="xMidYMid meet"></svg>
    </div>
    <div class="pvt-mainheader-nodeinfo">
        <div class="pvt-mainheader-nodeinfo-name"></div>
        <div class="pvt-mainheader-nodeinfo-subtitle"></div>
    </div>
    <div class="pvt-mainheader-nodeinfo-action">
    </div>
</div>`, r = ot(n), s = r.querySelector(".pvt-mainheader-icon"), o = r.querySelector(".pvt-mainheader-nodeinfo-name"), a = r.querySelector(".pvt-mainheader-nodeinfo-subtitle");
    if (s) {
      const c = Ds(e), l = ot(c);
      s.appendChild(l);
    }
    o && (o.textContent = `${t.length} nodes selected`), a && (a.textContent = `Out of ${this.uiManager.graph.getNodeCount()} total`), this.panel.appendChild(r), requestAnimationFrame(() => {
      var c, l;
      (l = (c = this.panel) == null ? void 0 : c.firstElementChild) == null || l.classList.add("enter-active");
    });
  }
  updateEdgesOverview(t) {
    if (!this.panel) return;
    if (this.renderCb) {
      this.renderCustomContent(t.map((a) => a.edge));
      return;
    }
    this.panel.innerHTML = "";
    const n = `<div class="enter-ready">
<div class="pvt-mainheader-nodepreview">
    ${pi(42)}
</div>
<div class="pvt-mainheader-nodeinfo">
    <div class="pvt-mainheader-nodeinfo-name"></div>
    <div class="pvt-mainheader-nodeinfo-subtitle"></div>
</div>
<div class="pvt-mainheader-nodeinfo-action">
</div>
</div>`, r = ot(n), s = r.querySelector(".pvt-mainheader-nodeinfo-name"), o = r.querySelector(".pvt-mainheader-nodeinfo-subtitle");
    s && (s.textContent = `${t.length} edges selected`), o && (o.textContent = `Out of ${this.uiManager.graph.getEdgeCount()} total`), this.panel.appendChild(r), requestAnimationFrame(() => {
      var a, c;
      (c = (a = this.panel) == null ? void 0 : a.firstElementChild) == null || c.classList.add("enter-active");
    });
  }
  /* Private methods */
  showTotalNodeCount() {
    if (!this.panel) return;
    const t = this.uiManager.graph.getMutableVisibleNodes().length, e = this.uiManager.graph.getMutableVisibleEdges().length;
    this.panel.textContent = `Showing ${t} nodes and ${e} edges`;
  }
}
function dp(i, t) {
  const e = t > 0 ? i / t * 100 : 0, n = document.createElement("span");
  n.style.display = "flex", n.style.alignItems = "center", n.style.gap = "0.5rem", n.style.fontFamily = "sans-serif", n.style.fontSize = "0.85rem", n.title = `${i} - ${e.toFixed(0)}%`;
  const r = document.createElement("span");
  r.classList.add("pivotick-inline-bar-container"), n.appendChild(r);
  const s = document.createElement("span");
  return s.classList.add("pivotick-inline-bar-fill"), s.style.width = `${e}%`, s.style.backgroundSize = `${100 / (e / 100)}% 100%`, r.appendChild(s), n;
}
const yn = "4dfd89de5d25fc9cc4b66c23d84b443af631c7dc", up = 6;
function bn(i, t, e) {
  const n = gp(i), r = document.createElement("div");
  for (const [s, o] of n) {
    const a = T("div", {
      class: "pvt-aggregated-property-section"
    }), c = T("span", {
      class: "pvt-aggregated-property-title"
    }, [`.${s}`]), l = T("div", {
      class: "pvt-aggregated-property-container"
    });
    let h = 0;
    for (const [d, u] of o) {
      if (h >= 10) {
        const v = T(
          "div",
          {},
          [
            T("div", {
              style: "text-align: center; font-weight: 300; font-size: 0.9rem; color: var(--pvt-text-color-5);"
            }, [
              `... ${o.size - h} more`
            ])
          ]
        );
        l.append(v);
        break;
      }
      let p = "";
      e && (p = wn(d) ? "" : e(s, d));
      const g = T(
        "div",
        {
          class: "pvt-aggregated-property-row"
        },
        [
          T("span", {
            class: [
              "pvt-aggregated-property-value",
              wn(d) ? "" : "code-container"
            ]
          }, [
            T("span", {}, [
              fp(pp(d), u),
              p
            ])
          ]),
          T("span", { class: "pvt-aggregated-property-count" }, [
            dp(u, t)
          ])
        ]
      );
      l.append(g), h++;
    }
    a.appendChild(c), a.appendChild(l), r.appendChild(a);
  }
  return r;
}
function pp(i) {
  return typeof i == "string" ? i : JSON.stringify(i);
}
function fp(i, t) {
  if (wn(i)) {
    let e = "", n = "";
    return Hs(i) ? (e = "- empty -", n = "The value is empty") : $s(i) && (e = `- ${t} other unique values -`, n = "All other values are unique"), T("span", { class: "pvt-aggregated-property-value-dim", title: n }, [
      e
    ]);
  }
  return document.createTextNode(i);
}
function Hs(i) {
  return i.length === 0;
}
function $s(i) {
  return i === yn;
}
function wn(i) {
  return Hs(i) || $s(i);
}
function Lr(i) {
  const t = /* @__PURE__ */ new Map();
  return i.forEach((e) => {
    e.forEach((n) => {
      if ((typeof n.name == "string" || typeof n.name == "number" || typeof n.name == "boolean") && (typeof n.value == "string" || typeof n.value == "number" || typeof n.value == "boolean")) {
        t.has(n.name) || t.set(n.name, /* @__PURE__ */ new Map());
        const r = t.get(n.name), s = r.get(n.value) || 0;
        r.set(n.value, s + 1);
      }
    });
  }), t;
}
function gp(i, t = !0) {
  const e = /* @__PURE__ */ new Map();
  for (const [o, a] of i.entries()) {
    const c = Array.from(a.entries()).sort(
      (l, h) => h[1] - l[1]
      // high count first
    );
    e.set(o, new Map(c));
  }
  const n = Array.from(e.entries()).sort(
    (o, a) => o[1].size - a[1].size
  ), r = new Map(n);
  if (!t)
    return r;
  const s = /* @__PURE__ */ new Map();
  for (const [o, a] of r)
    for (const [c, l] of a) {
      s.has(o) || s.set(o, /* @__PURE__ */ new Map());
      const h = s.get(o);
      if (a.size > up && l === 1) {
        const d = h.get(yn) || 0;
        h.set(yn, d + 1);
      } else
        h.set(c, l);
    }
  return s;
}
class mp {
  constructor(t) {
    f(this, "uiManager");
    f(this, "panel");
    f(this, "header");
    f(this, "body");
    f(this, "renderCb");
    this.uiManager = t, this.renderCb = typeof this.uiManager.getOptions().propertiesPanel.render == "function" ? this.uiManager.getOptions().propertiesPanel.render : void 0;
  }
  mount(t) {
    if (!t) return;
    const e = `
<div class="enter-ready">
    <div class="pvt-properties-header-panel pvt-sidebar-header-panel"></div>
    <div class="pvt-properties-body-panel pvt-sidebar-body-panel"></div>
</div>`;
    this.panel = ot(e), this.header = this.panel.querySelector(".pvt-properties-header-panel"), this.body = this.panel.querySelector(".pvt-properties-body-panel"), t.appendChild(this.panel);
  }
  destroy() {
    var t;
    (t = this.panel) == null || t.remove(), this.panel = void 0;
  }
  afterMount() {
    this.clearProperties();
  }
  clearProperties() {
    if (this.body) {
      if (this.renderCb) {
        this.renderCustomContent(null);
        return;
      }
      this.body.innerHTML = "", this.hidePanel();
    }
  }
  graphReady() {
  }
  renderCustomContent(t) {
    var n;
    if (!this.body || !this.renderCb) return;
    this.body.innerHTML = "";
    const e = St(this.renderCb, t);
    e && ((n = this.body) == null || n.appendChild(e));
  }
  setHeaderBasicNode() {
    this.header.textContent = "Basic Node Properties";
  }
  setHeaderBasicEdge() {
    this.header.textContent = "Basic Edge Properties";
  }
  setHeaderMultiSelectNode() {
    this.header.textContent = "Aggregated Node Properties";
  }
  setHeaderMultiSelectEdge() {
    this.header.textContent = "Aggregated Edge Properties";
  }
  showPanel() {
    this.panel.classList.add("enter-active");
  }
  hidePanel() {
    this.panel.classList.remove("enter-active");
  }
  /* Single selection */
  updateNodeProperties(t) {
    if (!this.body) return;
    if (this.setHeaderBasicNode(), this.showPanel(), this.renderCb) {
      this.renderCustomContent(t);
      return;
    }
    const n = ot(`
<div class="pvt-properties-container">
    <div class="dl-container">
    </div>
</div>`), r = n.querySelector(".dl-container");
    if (r) {
      const s = gn(t, this.uiManager.getOptions().propertiesPanel);
      r.append(si(s, t));
    }
    this.body.innerHTML = "", this.body.appendChild(n);
  }
  updateEdgeProperties(t) {
    if (!this.body) return;
    if (this.setHeaderBasicEdge(), this.showPanel(), this.renderCb) {
      this.renderCustomContent(t);
      return;
    }
    const n = ot(`
<div class="pvt-properties-container">
    <div class="dl-container">
    </div>
</div>`), r = n.querySelector(".dl-container");
    if (r) {
      const s = mn(t, this.uiManager.getOptions().propertiesPanel);
      r.append(si(s, t));
    }
    this.body.innerHTML = "", this.body.appendChild(n);
  }
  /* Multiple selection */
  updateNodesProperties(t) {
    if (!this.body) return;
    if (this.setHeaderMultiSelectNode(), this.showPanel(), this.renderCb) {
      this.renderCustomContent(t.map((s) => s.node));
      return;
    }
    const n = ot(`
<div class="pvt-properties-container">
    <div class="">
        <div class="pvt-aggregated-properties"></div>
    </div>
</div>`), r = n.querySelector("div.pvt-aggregated-properties");
    if (r) {
      const s = [];
      t.forEach((c) => {
        const { node: l } = c, h = gn(l, this.uiManager.getOptions().propertiesPanel);
        s.push(h);
      });
      const o = Lr(s), a = bn(o, t.length, this.genActionButtons.bind(this));
      r.appendChild(a);
    }
    this.body.innerHTML = "", this.body.appendChild(n);
  }
  updateEdgesProperties(t) {
    if (!this.body) return;
    if (this.setHeaderMultiSelectEdge(), this.showPanel(), this.renderCb) {
      this.renderCustomContent(t.map((s) => s.edge));
      return;
    }
    const n = ot(`
<div class="pvt-properties-container">
    <div class="">
        <div class="pvt-aggregated-properties"></div>
    </div>
</div>`), r = n.querySelector("div.pvt-aggregated-properties");
    if (r) {
      const s = [];
      t.forEach((c) => {
        const { edge: l } = c, h = mn(l, this.uiManager.getOptions().propertiesPanel);
        s.push(h);
      });
      const o = Lr(s), a = bn(o, t.length, this.genActionButtons.bind(this));
      r.appendChild(a);
    }
    this.body.innerHTML = "", this.body.appendChild(n);
  }
  genActionButtons(t, e) {
    const n = T("button", {
      title: "Select Similar"
    }, [Y({ svgIcon: Ps })]);
    n.addEventListener("click", () => {
      const o = this.uiManager.graph.renderer.getGraphInteraction().getSelectedNodes().filter((a) => a.node.getData()[t] != e);
      this.uiManager.graph.renderer.getGraphInteraction().removeNodesFromSelection(o);
    });
    const r = T("button", {
      title: "Exclude Similar"
    }, [Y({ svgIcon: Ts })]);
    return r.addEventListener("click", () => {
      const o = this.uiManager.graph.renderer.getGraphInteraction().getSelectedNodes().filter((a) => a.node.getData()[t] == e);
      this.uiManager.graph.renderer.getGraphInteraction().removeNodesFromSelection(o);
    }), T("div", { class: "pvt-aggregated-property-actions" }, [
      n,
      r
    ]);
  }
}
class vp {
  constructor(t) {
    f(this, "uiManager");
    f(this, "panelContainer");
    f(this, "panels");
    f(this, "allPanels", []);
    this.uiManager = t, this.panels = this.uiManager.getOptions().extraPanels;
  }
  mount(t) {
    t && (this.panelContainer = t);
  }
  destroy() {
    var t;
    (t = this.panelContainer) == null || t.remove(), this.panelContainer = void 0, this.allPanels = [];
  }
  afterMount() {
    this.mountPanels(), this.panels.forEach((t, e) => {
      t.alwaysVisible === !0 && this.showPanel(this.allPanels[e]);
    });
  }
  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  updateNode(t) {
    this.showAll();
  }
  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  updateEdge(t) {
    this.showAll();
  }
  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  updateNodes(t) {
    this.showAll();
  }
  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  updateEdges(t) {
    this.showAll();
  }
  clear() {
    this.hideAll();
  }
  showAll() {
    this.allPanels.forEach((t) => {
      this.showPanel(t);
    });
  }
  hideAll() {
    this.allPanels.forEach((t, e) => {
      this.panels[e].alwaysVisible !== !0 && this.hidePanel(t);
    });
  }
  showPanel(t) {
    t.classList.add("enter-active");
  }
  hidePanel(t) {
    t.classList.remove("enter-active");
  }
  mountPanels() {
    this.panelContainer && this.panels.forEach((t) => [
      this.mountPanel(t)
    ]);
  }
  mountPanel(t) {
    if (!this.panelContainer) return;
    const n = ot(`
            <div class="enter-ready">
                <div class="pivotick-extrapanel-header-panel pvt-sidebar-header-panel"></div>
                <div class="pivotick-extrapanel-body-panel pvt-sidebar-body-panel"></div>
            </div>`), r = n.querySelector(".pivotick-extrapanel-header-panel"), s = n.querySelector(".pivotick-extrapanel-body-panel"), o = St(t.title, null);
    o && r.appendChild(o);
    const a = St(t.render, null);
    a && s.appendChild(a), this.allPanels.push(n), this.panelContainer.appendChild(n);
  }
  graphReady() {
  }
}
function yp(i, t, e, n) {
  const r = document.createElement("div");
  r.className = "pivotick-tabs";
  const s = document.createElement("div");
  s.className = "pivotick-tab-controls";
  const o = document.createElement("div");
  o.className = "pivotick-tab-panels", n && e ? (n.appendChild(s), e.appendChild(o)) : e ? e.appendChild(r) : r.append(s, o);
  function a(l) {
    const h = l.id;
    o.querySelectorAll("[data-tab-panel]").forEach((p) => p.style.display = "none"), s.querySelectorAll(".pivotick-button").forEach((p) => {
      p.classList.toggle("pivotick-button-primary", !1), p.classList.toggle("pivotick-button-outline-secondary", !0);
    });
    const d = o.querySelector(`[data-tab-panel="${h}"]`), u = s.querySelector(`[data-tab-control="${h}"]`);
    d && (d.style.display = "block"), u && (u.classList.remove("pivotick-button-outline-secondary"), u.classList.add("pivotick-button-primary")), requestAnimationFrame(() => {
      l.onShown && (l == null || l.onShown());
    });
  }
  i.forEach((l) => {
    const h = ft({
      text: l.label,
      variant: "outline-secondary",
      "data-tab-control": l.id,
      onclick: () => a(l)
    });
    s.appendChild(h);
    const d = document.createElement("div");
    d.dataset.tabPanel = l.id, d.style.display = "none", d.appendChild(l.content), o.appendChild(d);
  });
  const c = i[0];
  return a(c), n && e ? o : r;
}
function Gs(i) {
  i.variant = i.variant ?? "primary";
  const {
    variant: t,
    size: e,
    iconUnicode: n,
    iconClass: r,
    svgIcon: s,
    imagePath: o,
    text: a,
    html: c,
    ...l
  } = i, h = document.createElement("span");
  h.classList.add("pivotick-badge"), h.classList.add(`pivotick-badge-${t}`), e && h.classList.add(`pivotick-badge-${e}`);
  for (const [p, g] of Object.entries(l))
    p === "class" ? Array.isArray(g) ? h.classList.add(...g) : h.classList.add(String(g)) : p in h ? h[p] = g : h.setAttribute(p, String(g));
  let d;
  n && (d = Y({ iconUnicode: n })), r && (d = Y({ iconClass: r })), s && (d = Y({ svgIcon: s })), o && (d = Y({ imagePath: o })), d && h.append(d);
  const u = document.createElement("text");
  return a && (d && (d.style.marginRight = "0.1em"), u.textContent = a), h.append(u), c && h.appendChild(c), h;
}
class bp {
  constructor(t) {
    f(this, "uiManager");
    f(this, "panel");
    f(this, "header");
    f(this, "body");
    f(this, "neighborCount");
    f(this, "egographContainer");
    f(this, "statContainer");
    f(this, "listContainer");
    f(this, "egoGraph");
    f(this, "renderCb");
    this.uiManager = t, this.renderCb = typeof this.uiManager.getOptions().neighborsPanel.render == "function" ? this.uiManager.getOptions().neighborsPanel.render : void 0;
  }
  mount(t) {
    if (!t) return;
    const e = `
<div class="enter-ready">
    <div class="pvt-neighbors-header-panel pvt-sidebar-header-panel"></div>
    <div class="pvt-neighbors-body-panel pvt-sidebar-body-panel"></div>
</div>`;
    this.panel = ot(e), this.header = this.panel.querySelector(".pvt-neighbors-header-panel"), this.body = this.panel.querySelector(".pvt-neighbors-body-panel"), this.neighborCount = T("div", { class: "pvt-neighbors-count" }), t.appendChild(this.panel), this.egographContainer = T("div", { class: "main-egograph-container" }, ["Egograph here"]), this.statContainer = T("div", { class: "main-stats-container" }, ["Stats here"]), this.listContainer = T("div", { class: "main-list-container" }, ["List here"]);
    const n = yp(
      [
        {
          id: "egograph",
          label: "Neighbor Graph",
          content: this.egographContainer,
          onShown: () => {
            requestAnimationFrame(async () => {
              this.egoGraph && (await this.egoGraph.simulation.start(), await this.egoGraph.simulation.waitForSimulationStop(), this.egoGraph.renderer.fitAndCenter());
            });
          }
        },
        {
          id: "stats",
          label: "Stats",
          content: this.statContainer
        },
        {
          id: "list",
          label: "List",
          content: this.listContainer
        }
      ],
      void 0,
      this.body,
      this.header
    );
    n.style.height = "100%", this.body.appendChild(this.neighborCount);
  }
  destroy() {
    var t;
    (t = this.panel) == null || t.remove(), this.panel = void 0;
  }
  afterMount() {
    this.clearNeighbors();
  }
  clearNeighbors() {
    if (this.body) {
      if (this.renderCb) {
        this.renderCustomContent(null);
        return;
      }
      this.renderCb ? this.body.innerHTML = "" : this.egographContainer && this.statContainer && this.listContainer && (this.egographContainer.innerHTML = "", this.statContainer.innerHTML = "", this.listContainer.innerHTML = ""), this.hidePanel();
    }
  }
  graphReady() {
  }
  renderCustomContent(t) {
    var n;
    if (!this.body || !this.renderCb) return;
    this.body.innerHTML = "";
    const e = St(this.renderCb, t);
    e && ((n = this.body) == null || n.appendChild(e));
  }
  showPanel() {
    this.panel.classList.add("enter-active");
  }
  hidePanel() {
    this.panel.classList.remove("enter-active");
  }
  /* Single selection */
  updateNodeNeighbors(t) {
    if (this.showPanel(), !this.neighborCount) return;
    if (this.renderCb) {
      this.renderCustomContent(t);
      return;
    }
    this.buildEgoGraph(t), this.buildList(t), this.buildStats(t);
    const e = t.degree(), n = e > 1 ? `${e} connections` : "1 connection";
    this.neighborCount.textContent = n;
  }
  updateEdgeNeighbors(t) {
    if (this.showPanel(), this.renderCb) {
      this.renderCustomContent(t);
      return;
    }
  }
  /* Multiple selection */
  updateNodesNeighbors(t) {
    if (this.showPanel(), !this.neighborCount) return;
    if (this.renderCb) {
      this.renderCustomContent(t.map((s) => s.node));
      return;
    }
    if (t.length <= 1) return;
    const e = this.mergeNodesIntoNode(t.map((s) => s.node));
    this.buildEgoGraph(e, !1), this.buildList(e), this.buildStats(e);
    const n = e.degree(), r = n > 1 ? `${n} connections` : "1 connection";
    this.neighborCount.textContent = r;
  }
  updateEdgesNeighbors(t) {
    if (this.showPanel(), this.renderCb) {
      this.renderCustomContent(t.map((e) => e.edge));
      return;
    }
  }
  buildEgoGraph(t, e = !0) {
    if (!this.egographContainer) return;
    this.egographContainer.innerHTML = "", this.egoGraph && this.egoGraph.destroy(), this.egographContainer.style.visibility = "hidden";
    const n = /* @__PURE__ */ new Map();
    for (const l of [
      t,
      ...t.getConnectedNodes(),
      ...t.getConnectingNodes()
    ])
      n.set(l.id.toString(), l);
    const r = [
      ...t.getEdgesOut(),
      ...t.getEdgesIn()
    ], s = /* @__PURE__ */ new Map();
    r.forEach((l) => {
      !l || l.id == null || s.set(l.id.toString(), l);
    }), n.forEach((l) => {
      l.getEdgesOut().forEach((h) => {
        const d = h.to;
        n.has(d.id.toString()) && d.id !== t.id && s.set(h.id.toString(), h);
      });
    });
    const a = {
      nodes: [...n.values()].filter((l) => {
        var h;
        return l.getDeepestNodeClone() === void 0 ? !0 : ((h = l.getDeepestNodeClone()) == null ? void 0 : h.visible) ?? !1;
      }).map((l) => l.toDict(!0)),
      edges: [...s.values()].map((l) => l.toDict())
    }, c = {
      UI: {
        mode: "viewer",
        tooltip: {
          enabled: !1,
          allowPinning: !1
        },
        contextMenu: {
          enabled: !1
        },
        navigation: {
          enabled: !1
        }
      },
      layout: {
        type: "egoTree",
        radial: !0,
        radialGap: 120,
        rootId: t.id
      },
      render: {
        ...this.uiManager.graph.getOptions().render,
        dragEnabled: !1,
        enableFocusMode: !1,
        enableNodeExpansion: !1,
        interactionEnabled: !0,
        zoomEnabled: !1,
        zoomAnimationDuration: 100
      },
      simulation: {
        useWorker: !1,
        warmupTicks: 0,
        cooldownTime: 0
      },
      callbacks: {
        onNodeHoverIn: (l, h) => {
          const d = this.uiManager.graph.getMutableNode(h.id);
          d && this.uiManager.graph.highlightElement(d);
        },
        onNodeHoverOut: (l, h) => {
          const d = this.uiManager.graph.getMutableNode(h.id);
          d && this.uiManager.graph.unHighlightElement(d);
        }
      }
    };
    this.egoGraph = new bt(this.egographContainer, a, c), this.egoGraph.on("ready", () => {
      setTimeout(() => {
        this.egographContainer.style.visibility = "visible";
      }, 20), e && this.egoGraph.selectElement(this.egoGraph.getMutableNode(t.id));
    });
  }
  buildList(t) {
    if (!this.listContainer) return;
    this.listContainer.innerHTML = "";
    const e = 26, n = [
      ...t.getEdgesOut(),
      ...t.getEdgesIn()
    ];
    n.sort((s, o) => {
      const a = s.from.id === t.id ? s.to : s.from, c = o.from.id === t.id ? o.to : o.from, l = Wt(a, this.uiManager.getOptions().mainHeader), h = Wt(c, this.uiManager.getOptions().mainHeader);
      return l.localeCompare(h);
    });
    const r = T("div", { class: "" });
    for (const s of n) {
      const o = s.from.id === t.id, a = o ? s.to : s.from, c = be(s, this.uiManager.getOptions().mainHeader) || "", l = Y(o ? { svgIcon: Qu } : { svgIcon: Zu });
      l.classList.add("edge"), l.classList.add(o ? "edge-out" : "edge-in"), l.setAttribute("title", o ? "Outgoing edge" : "Incoming edge");
      const h = Wt(a, this.uiManager.getOptions().mainHeader), d = document.createElement("template");
      d.innerHTML = `
            <div class="pvt-neighbors-list__nodecontainer">
                <span class="pvt-neighbors-list__nodepreview">
                    <svg class="pvt-mainheader-icon" width="${e}" height="${e}" viewBox="0 0 ${e} ${e}" preserveAspectRatio="xMidYMid meet"></svg>
                </span>
                ${h}
            </div>`;
      const u = d.content.firstElementChild, p = u.querySelector(".pvt-neighbors-list__nodepreview .pvt-mainheader-icon") ?? void 0, g = a.getGraphElement();
      if (p && g && g instanceof SVGGElement) {
        const x = g.cloneNode(!0), S = g.getBBox(), C = e / Math.max(S.width, S.height);
        x.setAttribute(
          "transform",
          `translate(${(e - S.width * C) / 2 - S.x * C}, ${(e - S.height * C) / 2 - S.y * C}) scale(${C})`
        ), p.appendChild(x);
      }
      const v = Gs({
        text: c || "- empty -",
        size: "sm",
        variant: "secondary",
        class: ["pvt-neighbor-edge-description", c || "empty-label"]
      }), b = T(
        "div",
        {
          class: "edge-details"
        },
        [
          l,
          u,
          v
        ]
      );
      r.appendChild(b);
    }
    this.listContainer.appendChild(r);
  }
  buildStats(t) {
    if (!this.statContainer) return;
    this.statContainer.innerHTML = "";
    const e = T("dl", { class: "pvt-property-list" }), n = T(
      "dl",
      {
        class: "pvt-property-row"
      },
      [
        T("dt", { class: "pvt-property-name", title: "Total connections", style: "font-size: 1em;" }, ["Degree"]),
        T("dd", { class: "pvt-property-value", style: "display: flex; align-items: center; font-size: 1em;" }, [
          T("span", { style: "margin-right: 8px;" }, [t.degree().toString()]),
          T("span", {
            style: "display: inline-flex; align-items: center; margin-right: 8px; color: var(--pvt-text-color-secondary)",
            title: "Outgoing edges"
          }, [Y({ svgIcon: rp }), t.getEdgesOut().length.toString()]),
          T("span", {
            style: "display: inline-flex; align-items: center; color: var(--pvt-text-color-secondary)",
            title: "Incoming edges"
          }, [Y({ svgIcon: sp }), t.getEdgesIn().length.toString()])
        ])
      ]
    );
    e.append(n);
    const r = T("div", { class: "core-stats" }, [e]), s = /* @__PURE__ */ new Map();
    [
      ...t.getEdgesOut(),
      ...t.getEdgesIn()
    ].forEach((h) => {
      const d = be(h, this.uiManager.getOptions().mainHeader) || "", u = s.get(d) || 0;
      s.set(d, u + 1);
    });
    const a = /* @__PURE__ */ new Map();
    a.set("Label", s);
    const c = bn(a, t.degree(), this.genActionButtonsSingleSelection.bind(this)), l = T("div", { class: "aggregated-labels" }, [c]);
    this.statContainer.appendChild(r), this.statContainer.appendChild(l);
  }
  genActionButtonsSingleSelection(t, e) {
    const n = T("button", {
      title: "Select nodes linked with this label"
    }, [Y({ svgIcon: Ps })]);
    n.addEventListener("click", () => {
      const o = this.getNodesMatchingFilteredEdgeName(e);
      o && (this.uiManager.graph.renderer.getGraphInteraction().clearNodeSelectionList(), o.length > 1 ? this.uiManager.graph.renderer.getGraphInteraction().selectNodes(o) : this.uiManager.graph.renderer.getGraphInteraction().selectNode(o[0].element, o[0].node));
    });
    const r = T("button", {
      title: "Exclude nodes linked with this label"
    }, [Y({ svgIcon: Ts })]);
    return r.addEventListener("click", () => {
      const o = this.getNodesMatchingFilteredEdgeName(e, !0);
      o && (this.uiManager.graph.renderer.getGraphInteraction().clearNodeSelectionList(), o.length > 1 ? this.uiManager.graph.renderer.getGraphInteraction().selectNodes(o) : this.uiManager.graph.renderer.getGraphInteraction().selectNode(o[0].element, o[0].node));
    }), T("div", { class: "pvt-aggregated-property-actions" }, [
      n,
      r
    ]);
  }
  getNodesMatchingFilteredEdgeName(t, e = !1) {
    const n = this.uiManager.graph.renderer.getGraphInteraction().getSelectedNode();
    if (!n) return;
    const r = n.node, s = [...r.getEdgesOut(), ...r.getEdgesIn()], o = /* @__PURE__ */ new Map();
    return s.filter((a) => {
      const c = be(a, this.uiManager.getOptions().mainHeader);
      return e ? c !== t : c === t;
    }).forEach((a) => {
      const c = r === a.from ? a.to : a.from;
      o.set(c.id.toString(), c);
    }), [...o.values()].map((a) => ({
      node: a,
      element: a.getGraphElement()
    }));
  }
  mergeNodesIntoNode(t) {
    const e = {
      size: 50,
      shape: "square",
      color: "transparent",
      strokeColor: "transparent",
      html: (l) => {
        const d = l.getData().aggregated_node_count, u = Y({ svgIcon: Ds(28) });
        return u.style = "position: absolute;", ot(`<div style="display: flex; flex-direction: column; position: relative; align-items: center;">
                    ${u.outerHTML}
                    <div style="
    height: 65%;
    width: 65%;
    margin-top: 18%;
    display: flex;
    align-items: center;
    flex-direction: column;
    justify-content: center;
    background-color: var(--pvt-bg-color-5);">
                        <div style="height: auto; font-weight: 600; font-size: 1.5em;">+${d}</div>
                        <div style="height: auto;">Group</div>
                    </div>
                </div>`);
      }
    }, n = { label: `${t.length} nodes`, aggregated_node_count: t.length }, r = new Mt("aggregated-node", n, e);
    r.weight = 10;
    const s = new Set(t.map((l) => l.id.toString())), o = t.flatMap((l) => [
      ...l.getEdgesOut(),
      ...l.getEdgesIn()
    ]), a = [], c = [];
    for (const l of o) {
      const h = s.has(l.from.id), d = s.has(l.to.id);
      h !== d && (h ? a.push(l) : c.push(l));
    }
    return a.forEach((l, h) => {
      const d = l.to.clone();
      new _t(`outgoing-${h}`, r, d, l.getData(), l.getStyle());
    }), c.forEach((l, h) => {
      const d = l.from.clone();
      new _t(`incoming-${h}`, d, r, l.getData(), l.getStyle());
    }), r;
  }
}
class wp {
  constructor(t) {
    f(this, "uiManager");
    f(this, "sidebar");
    f(this, "sidebarOpen", !0);
    f(this, "sidebarMainHeader");
    f(this, "sidebarProperties");
    f(this, "sidebarNeighbors");
    f(this, "extraPanelManager");
    f(this, "mainHeaderPanel");
    f(this, "mainBodyPanel");
    f(this, "neighborPanel");
    f(this, "extraPanelContainer");
    f(this, "collapse");
    this.uiManager = t, this.sidebarMainHeader = new hp(this.uiManager), this.sidebarProperties = new mp(this.uiManager), this.sidebarNeighbors = new bp(this.uiManager), this.extraPanelManager = new vp(this.uiManager);
  }
  mount(t) {
    if (!t) return;
    const e = `
<div class="pvt-sidebar-elements">
    <div class="pvt-mainheader-panel"></div>
    <div class="pvt-sidebar-separator"></div>
    <div class="pvt-properties-panel pvt-sidebar-panel"></div>
    <div class="pvt-sidebar-separator"></div>
    <div class="pvt-neighbor-panel pvt-sidebar-panel"></div>
    <div class="pvt-sidebar-separator"></div>
    <div class="pvt-extra-panel pvt-sidebar-panel"></div>
</div>`;
    this.sidebar = ot(e), t.appendChild(this.sidebar);
  }
  destroy() {
    var t;
    this.sidebarMainHeader.destroy(), this.sidebarProperties.destroy(), (t = this.sidebar) == null || t.remove(), this.sidebar = void 0;
  }
  afterMount() {
    var t, e;
    this.sidebar && (this.mainHeaderPanel = this.sidebar.querySelector(".pvt-mainheader-panel") ?? void 0, this.sidebarMainHeader.mount(this.mainHeaderPanel), this.mainBodyPanel = this.sidebar.querySelector(".pvt-properties-panel") ?? void 0, this.sidebarProperties.mount(this.mainBodyPanel), this.neighborPanel = this.sidebar.querySelector(".pvt-neighbor-panel") ?? void 0, this.sidebarNeighbors.mount(this.neighborPanel), this.extraPanelContainer = this.sidebar.querySelector(".pvt-extra-panel") ?? void 0, this.extraPanelManager.mount(this.extraPanelContainer), this.collapse = T("span", { class: "pvt-sidebar-collapse-container" }, [
      T("span", { class: "pvt-sidebar-collapse-button pvt-sidebar-collapse-button-collapse" }, [Y({ svgIcon: Pu })]),
      T("span", { class: "pvt-sidebar-collapse-button pvt-sidebar-collapse-button-expand" }, [Y({ svgIcon: Tu })])
    ]), this.sidebar.parentElement.appendChild(this.collapse), ((e = (t = this.uiManager.getOptions()) == null ? void 0 : t.sidebar) == null ? void 0 : e.collapsed) === !0 ? this.hideSidebar() : this.showSidebar(), this.sidebarMainHeader.afterMount(), this.sidebarProperties.afterMount(), this.sidebarNeighbors.afterMount(), this.extraPanelManager.afterMount());
  }
  graphReady() {
    var t;
    this.sidebarMainHeader.graphReady(), this.sidebarProperties.graphReady(), this.sidebarNeighbors.graphReady(), this.extraPanelManager.graphReady(), this.uiManager.graph.renderer.getGraphInteraction().on("selectNode", (e, n) => {
      this.sidebarMainHeader.updateNodeOverview(e, n), this.sidebarProperties.updateNodeProperties(e), this.sidebarNeighbors.updateNodeNeighbors(e), this.extraPanelManager.updateNode(e);
    }), this.uiManager.graph.renderer.getGraphInteraction().on("unselectNode", () => {
      this.sidebarMainHeader.clearOverview(), this.sidebarProperties.clearProperties(), this.sidebarNeighbors.clearNeighbors(), this.extraPanelManager.clear();
    }), this.uiManager.graph.renderer.getGraphInteraction().on("selectEdge", (e) => {
      this.sidebarMainHeader.updateEdgeOverview(e), this.sidebarProperties.updateEdgeProperties(e), this.sidebarNeighbors.updateEdgeNeighbors(e), this.extraPanelManager.updateEdge(e);
    }), this.uiManager.graph.renderer.getGraphInteraction().on("unselectEdge", () => {
      this.sidebarMainHeader.clearOverview(), this.sidebarProperties.clearProperties(), this.sidebarNeighbors.clearNeighbors(), this.extraPanelManager.clear();
    }), this.uiManager.graph.renderer.getGraphInteraction().on("selectNodes", (e) => {
      const n = this.uiManager.graph.renderer.getGraphInteraction().getSelectedNodes();
      this.sidebarMainHeader.updateNodesOverview(n), this.sidebarProperties.updateNodesProperties(n), this.sidebarNeighbors.updateNodesNeighbors(n), this.extraPanelManager.updateNodes(n);
    }), this.uiManager.graph.renderer.getGraphInteraction().on("unselectNodes", () => {
      const e = this.uiManager.graph.renderer.getGraphInteraction().getSelectedNodes();
      e.length > 0 ? (this.sidebarMainHeader.updateNodesOverview(e), this.sidebarProperties.updateNodesProperties(e), this.sidebarNeighbors.updateNodesNeighbors(e), this.extraPanelManager.updateNodes(e)) : (this.sidebarMainHeader.clearOverview(), this.sidebarProperties.clearProperties(), this.sidebarNeighbors.clearNeighbors(), this.extraPanelManager.clear());
    }), this.uiManager.graph.renderer.getGraphInteraction().on("selectEdges", (e) => {
      this.sidebarMainHeader.updateEdgesOverview(e), this.sidebarProperties.updateEdgesProperties(e), this.sidebarNeighbors.updateEdgesNeighbors(e), this.extraPanelManager.updateEdges(e);
    }), this.uiManager.graph.renderer.getGraphInteraction().on("unselectEdges", () => {
      this.sidebarMainHeader.clearOverview(), this.sidebarProperties.clearProperties(), this.sidebarNeighbors.clearNeighbors(), this.extraPanelManager.clear();
    }), (t = this.collapse) == null || t.addEventListener("click", () => {
      this.toggleSidebar();
    });
  }
  toggleSidebar() {
    this.sidebar.closest(".pvt-sidebar").classList.toggle("pvt-sidebar-collapsed", this.sidebarOpen), this.sidebarOpen = !this.sidebarOpen;
  }
  showSidebar() {
    this.sidebar.closest(".pvt-sidebar").classList.remove("pvt-sidebar-collapsed"), this.sidebarOpen = !0;
  }
  hideSidebar() {
    this.sidebar.closest(".pvt-sidebar").classList.add("pvt-sidebar-collapsed"), this.sidebarOpen = !1;
  }
}
class xp {
  constructor(t, e = {}) {
    f(this, "uiManager");
    f(this, "options");
    f(this, "slidePanel");
    f(this, "header");
    f(this, "body");
    f(this, "isOpen", !1);
    f(this, "DEFAULT_HEADER", null);
    f(this, "DEFAULT_BODY", "- empty panel -");
    this.uiManager = t, this.options = e, this.options.header || (this.options.header = this.DEFAULT_HEADER), this.options.body || (this.options.body = this.DEFAULT_BODY);
  }
  mount(t) {
    if (!t) return;
    const e = document.createElement("template");
    if (e.innerHTML = `
  <div class="pvt-slide-panel" id="pvt-side-panel">
  </div>
`, this.slidePanel = e.content.firstElementChild, this.slidePanel.innerHTML = "", this.options.header != null) {
      this.header = document.createElement("div"), this.header.className = "pvt-slide-panel__header", this.setHeader(this.options.header), this.slidePanel.appendChild(this.header);
      const n = ft({
        text: "×",
        onClick: () => {
          this.close();
        },
        id: "pvt-sidePanel-close",
        class: "pvt-close-button",
        style: "margin-left: auto;"
      });
      this.header.appendChild(n);
    }
    this.body = document.createElement("div"), this.body.className = "pvt-slide-panel__content", this.setBody(this.options.body), this.slidePanel.appendChild(this.body), this.options.noBodyPadding ? this.body.style.padding = "0" : this.body.style.padding = "", t.appendChild(this.slidePanel);
  }
  destroy() {
    var t;
    (t = this.slidePanel) == null || t.remove(), this.slidePanel = void 0;
  }
  afterMount() {
  }
  graphReady() {
  }
  open() {
    var t;
    this.isOpen = !0, (t = this.slidePanel) == null || t.classList.add("open");
  }
  close() {
    var t;
    this.isOpen = !1, (t = this.slidePanel) == null || t.classList.remove("open");
  }
  toggle() {
    this.isOpen ? this.close() : this.open();
  }
  setHeader(t) {
    this.header && (this.header.innerHTML = "", t && (this.options.header instanceof HTMLElement ? this.header.appendChild(this.options.header) : this.options.rawHeader ? this.header.innerHTML = this.options.header : this.header.textContent = this.options.header));
  }
  setBody(t) {
    this.body && (this.body.innerHTML = "", t && (t instanceof HTMLElement ? this.body.appendChild(t) : this.options.rawBody ? this.body.innerHTML = t : this.body.textContent = t));
  }
}
class Cp {
  constructor(t) {
    f(this, "uiManager");
    f(this, "searchBox");
    f(this, "searchInput");
    f(this, "searchResultsContainer");
    f(this, "searchSummaryContainer");
    f(this, "results");
    f(this, "highlightedIndex", 0);
    f(this, "MAX_RESULT_COUNT", 12);
    this.uiManager = t;
  }
  mount(t) {
    t && (this.searchBox = this.build(), t.appendChild(this.searchBox));
  }
  build() {
    var e, n;
    const t = document.createElement("template");
    return t.innerHTML = `
  <div id="pvt-searchbox" class="pvt-searchbox">
    <div class="search-container">
        <div class="input-container">
            <span class="icon-container">${Fs}</span>
            <input id="pvt-search-input" type="text" name="pvt-search" placeholder="Search" class="search-text" autocomplete="off" />
        </div>
    </div>
    <div class="pvt-search-results"></div>
    <div class="pvt-search-summary"></div>
    <div class="pvt-search-hints">
        <span>
            <span class="pvt-search-icon">${Wu}</span>
            <span class="pvt-search-icon">${Ku}</span>
            <span class="pvt-search-text">to navigate</span>
        </span>
        <span>
            <span class="pvt-search-icon">${Ju}</span>
            <span class="pvt-search-text">to select</span>
        </span>
        <span>
            <span class="pvt-search-icon">esc</span>
            <span class="pvt-search-text">to close</span>
        </span>
    </div>
  </div>
`, this.searchBox = t.content.firstElementChild, this.searchInput = this.searchBox.querySelector("#pvt-search-input") ?? void 0, this.searchResultsContainer = this.searchBox.querySelector(".pvt-search-results") ?? void 0, this.searchSummaryContainer = this.searchBox.querySelector(".pvt-search-summary") ?? void 0, (e = this.searchInput) == null || e.addEventListener("input", () => {
      this.searchAndShowResults(this.searchInput.value), this.updateHighlight();
    }), (n = this.searchInput) == null || n.addEventListener("keydown", (r) => {
      var o;
      if (r.key == "Escape") {
        this.dispatchEvent("pvt-searchbox-close");
        return;
      }
      if (!this.results || this.results.length < 1) return;
      const s = Math.min(this.MAX_RESULT_COUNT, this.results.length);
      switch (r.key) {
        case "ArrowDown":
          r.preventDefault(), this.highlightedIndex = (this.highlightedIndex + 1) % s, this.updateHighlight();
          break;
        case "ArrowUp":
          r.preventDefault(), this.highlightedIndex = (this.highlightedIndex - 1 + s) % s, this.updateHighlight();
          break;
        case "Enter":
          if (r.preventDefault(), this.highlightedIndex >= 0) {
            const a = (o = this.searchResultsContainer) == null ? void 0 : o.children[this.highlightedIndex];
            a == null || a.click();
          }
          break;
      }
    }), this.searchBox;
  }
  destroy() {
    var t;
    (t = this.searchBox) == null || t.remove(), this.searchBox = void 0;
  }
  afterMount() {
  }
  graphReady() {
  }
  buildResult(t) {
    const n = document.createElement("template");
    n.innerHTML = `
  <div class="pvt-search-result">
    <div>
        <div class="pvt-search-result__nodepreview">
            <svg class="pvt-mainheader-icon" width="30" height="30" viewBox="0 0 30 30" preserveAspectRatio="xMidYMid meet"></svg>
        </div>
        <div class="pvt-search-result__name"></div>
    </div>
    <div class="pvt-search-result__info">
        <div class="pvt-search-result__info_key"></div>
        <div class="pvt-search-result__info_value"></div>
    </div>
  </div>
`;
    const r = t[0], s = t[1], o = n.content.firstElementChild, a = o.querySelector(".pvt-search-result__nodepreview .pvt-mainheader-icon") ?? void 0, c = o.querySelector(".pvt-search-result__name") ?? void 0, l = o.querySelector(".pvt-search-result__info_key") ?? void 0, h = o.querySelector(".pvt-search-result__info_value") ?? void 0;
    o.addEventListener("click", () => {
      this.clickHandler(r);
    });
    const d = r.getGraphElement();
    if (d && d instanceof SVGGElement) {
      const u = d.cloneNode(!0), p = d.getBBox(), g = 30 / Math.max(p.width, p.height);
      u.setAttribute(
        "transform",
        `translate(${(30 - p.width * g) / 2 - p.x * g}, ${(30 - p.height * g) / 2 - p.y * g}) scale(${g})`
      ), a.appendChild(u);
    }
    return c.textContent = Wt(r, this.uiManager.getOptions().mainHeader), l.textContent = `.${s.key}: `, h.textContent = s.value, o;
  }
  updateHighlight() {
    !this.results || !this.searchResultsContainer || this.results.forEach((t, e) => {
      var r;
      const n = (r = this.searchResultsContainer) == null ? void 0 : r.children[e];
      n && (e === this.highlightedIndex ? n.classList.add("active") : n.classList.remove("active"));
    });
  }
  search(t) {
    const e = [], n = t.trim().toLowerCase();
    if (!(!n || n.length < 2)) {
      for (const r of this.uiManager.graph.getMutableNodes()) {
        const s = r.getData();
        for (const o in s) {
          const a = s[o];
          if (a == null) continue;
          const c = String(a).toLowerCase();
          let l = n.startsWith('"') ? n.slice(1) : n;
          const h = n.startsWith('"') && n.endsWith('"');
          if (h && (l = l.slice(0, -1).trim()), h ? c === l : c.includes(l)) {
            const u = { key: o, value: String(a) };
            e.push([r, u]);
            break;
          }
        }
      }
      return e;
    }
  }
  clickHandler(t) {
    this.dispatchEvent("pvt-searchbox-select", t);
  }
  searchAndShowResults(t) {
    if (!(!this.searchResultsContainer || !this.searchSummaryContainer) && (this.results = void 0, this.searchResultsContainer.innerHTML = "", this.searchSummaryContainer.innerHTML = "", this.results = this.search(t), this.results)) {
      const e = [];
      for (const n of this.results) {
        if (e.length >= this.MAX_RESULT_COUNT) break;
        e.push(this.buildResult(n));
      }
      e.forEach((n) => {
        var r;
        (r = this.searchResultsContainer) == null || r.appendChild(n);
      }), this.searchSummaryContainer.appendChild(this.createSummary());
    }
  }
  createSummary() {
    if (!this.results) return document.createElement("div");
    let t = "";
    this.results.length === 0 ? t = "No results found" : this.results.length > this.MAX_RESULT_COUNT ? t = `Showing top ${this.MAX_RESULT_COUNT} of ${this.results.length} results` : t = `${this.results.length} results`;
    const e = document.createElement("template");
    return e.innerHTML = `
  <div>
    ${t}
  </div>
`, e.content.firstElementChild;
  }
  dispatchEvent(t, e) {
    if (!this.searchBox) return;
    const n = new CustomEvent(t, {
      detail: e,
      bubbles: !0,
      cancelable: !0
    });
    this.searchBox.dispatchEvent(n);
  }
}
function Wi(i, t) {
  i.split(/\s+/).forEach((e) => {
    t(e);
  });
}
class Mp {
  constructor() {
    this._events = {};
  }
  on(t, e) {
    Wi(t, (n) => {
      const r = this._events[n] || [];
      r.push(e), this._events[n] = r;
    });
  }
  off(t, e) {
    var n = arguments.length;
    if (n === 0) {
      this._events = {};
      return;
    }
    Wi(t, (r) => {
      if (n === 1) {
        delete this._events[r];
        return;
      }
      const s = this._events[r];
      s !== void 0 && (s.splice(s.indexOf(e), 1), this._events[r] = s);
    });
  }
  trigger(t, ...e) {
    var n = this;
    Wi(t, (r) => {
      const s = n._events[r];
      s !== void 0 && s.forEach((o) => {
        o.apply(n, e);
      });
    });
  }
}
function Ep(i) {
  return i.plugins = {}, class extends i {
    constructor() {
      super(...arguments), this.plugins = {
        names: [],
        settings: {},
        requested: {},
        loaded: {}
      };
    }
    /**
     * Registers a plugin.
     *
     * @param {function} fn
     */
    static define(t, e) {
      i.plugins[t] = {
        name: t,
        fn: e
      };
    }
    /**
     * Initializes the listed plugins (with options).
     * Acceptable formats:
     *
     * List (without options):
     *   ['a', 'b', 'c']
     *
     * List (with options):
     *   [{'name': 'a', options: {}}, {'name': 'b', options: {}}]
     *
     * Hash (with options):
     *   {'a': { ... }, 'b': { ... }, 'c': { ... }}
     *
     * @param {array|object} plugins
     */
    initializePlugins(t) {
      var e, n;
      const r = this, s = [];
      if (Array.isArray(t))
        t.forEach((o) => {
          typeof o == "string" ? s.push(o) : (r.plugins.settings[o.name] = o.options, s.push(o.name));
        });
      else if (t)
        for (e in t)
          t.hasOwnProperty(e) && (r.plugins.settings[e] = t[e], s.push(e));
      for (; n = s.shift(); )
        r.require(n);
    }
    loadPlugin(t) {
      var e = this, n = e.plugins, r = i.plugins[t];
      if (!i.plugins.hasOwnProperty(t))
        throw new Error('Unable to find "' + t + '" plugin');
      n.requested[t] = !0, n.loaded[t] = r.fn.apply(e, [e.plugins.settings[t] || {}]), n.names.push(t);
    }
    /**
     * Initializes a plugin.
     *
     */
    require(t) {
      var e = this, n = e.plugins;
      if (!e.plugins.loaded.hasOwnProperty(t)) {
        if (n.requested[t])
          throw new Error('Plugin has circular dependency ("' + t + '")');
        e.loadPlugin(t);
      }
      return n.loaded[t];
    }
  };
}
const Ci = (i) => (i = i.filter(Boolean), i.length < 2 ? i[0] || "" : _p(i) == 1 ? "[" + i.join("") + "]" : "(?:" + i.join("|") + ")"), qs = (i) => {
  if (!Sp(i))
    return i.join("");
  let t = "", e = 0;
  const n = () => {
    e > 1 && (t += "{" + e + "}");
  };
  return i.forEach((r, s) => {
    if (r === i[s - 1]) {
      e++;
      return;
    }
    n(), t += r, e = 1;
  }), n(), t;
}, Vs = (i) => {
  let t = Array.from(i);
  return Ci(t);
}, Sp = (i) => new Set(i).size !== i.length, ke = (i) => (i + "").replace(/([\$\(\)\*\+\.\?\[\]\^\{\|\}\\])/gu, "\\$1"), _p = (i) => i.reduce((t, e) => Math.max(t, kp(e)), 0), kp = (i) => Array.from(i).length, Us = (i) => {
  if (i.length === 1)
    return [[i]];
  let t = [];
  const e = i.substring(1);
  return Us(e).forEach(function(r) {
    let s = r.slice(0);
    s[0] = i.charAt(0) + s[0], t.push(s), s = r.slice(0), s.unshift(i.charAt(0)), t.push(s);
  }), t;
}, Np = [[0, 65535]], Ap = "[̀-ͯ·ʾʼ]";
let fi, js;
const Ip = 3, Dn = {}, Or = {
  "/": "⁄∕",
  0: "߀",
  a: "ⱥɐɑ",
  aa: "ꜳ",
  ae: "æǽǣ",
  ao: "ꜵ",
  au: "ꜷ",
  av: "ꜹꜻ",
  ay: "ꜽ",
  b: "ƀɓƃ",
  c: "ꜿƈȼↄ",
  d: "đɗɖᴅƌꮷԁɦ",
  e: "ɛǝᴇɇ",
  f: "ꝼƒ",
  g: "ǥɠꞡᵹꝿɢ",
  h: "ħⱨⱶɥ",
  i: "ɨı",
  j: "ɉȷ",
  k: "ƙⱪꝁꝃꝅꞣ",
  l: "łƚɫⱡꝉꝇꞁɭ",
  m: "ɱɯϻ",
  n: "ꞥƞɲꞑᴎлԉ",
  o: "øǿɔɵꝋꝍᴑ",
  oe: "œ",
  oi: "ƣ",
  oo: "ꝏ",
  ou: "ȣ",
  p: "ƥᵽꝑꝓꝕρ",
  q: "ꝗꝙɋ",
  r: "ɍɽꝛꞧꞃ",
  s: "ßȿꞩꞅʂ",
  t: "ŧƭʈⱦꞇ",
  th: "þ",
  tz: "ꜩ",
  u: "ʉ",
  v: "ʋꝟʌ",
  vy: "ꝡ",
  w: "ⱳ",
  y: "ƴɏỿ",
  z: "ƶȥɀⱬꝣ",
  hv: "ƕ"
};
for (let i in Or) {
  let t = Or[i] || "";
  for (let e = 0; e < t.length; e++) {
    let n = t.substring(e, e + 1);
    Dn[n] = i;
  }
}
const Lp = new RegExp(Object.keys(Dn).join("|") + "|" + Ap, "gu"), Op = (i) => {
  fi === void 0 && (fi = Fp(Np));
}, Tr = (i, t = "NFKD") => i.normalize(t), gi = (i) => Array.from(i).reduce(
  /**
   * @param {string} result
   * @param {string} char
   */
  (t, e) => t + Tp(e),
  ""
), Tp = (i) => (i = Tr(i).toLowerCase().replace(Lp, (t) => Dn[t] || ""), Tr(i, "NFC"));
function* Pp(i) {
  for (const [t, e] of i)
    for (let n = t; n <= e; n++) {
      let r = String.fromCharCode(n), s = gi(r);
      s != r.toLowerCase() && (s.length > Ip || s.length != 0 && (yield { folded: s, composed: r, code_point: n }));
    }
}
const Dp = (i) => {
  const t = {}, e = (n, r) => {
    const s = t[n] || /* @__PURE__ */ new Set(), o = new RegExp("^" + Vs(s) + "$", "iu");
    r.match(o) || (s.add(ke(r)), t[n] = s);
  };
  for (let n of Pp(i))
    e(n.folded, n.folded), e(n.folded, n.composed);
  return t;
}, Fp = (i) => {
  const t = Dp(i), e = {};
  let n = [];
  for (let s in t) {
    let o = t[s];
    o && (e[s] = Vs(o)), s.length > 1 && n.push(ke(s));
  }
  n.sort((s, o) => o.length - s.length);
  const r = Ci(n);
  return js = new RegExp("^" + r, "u"), e;
}, zp = (i, t = 1) => {
  let e = 0;
  return i = i.map((n) => (fi[n] && (e += n.length), fi[n] || n)), e >= t ? qs(i) : "";
}, Bp = (i, t = 1) => (t = Math.max(t, i.length - 1), Ci(Us(i).map((e) => zp(e, t)))), Pr = (i, t = !0) => {
  let e = i.length > 1 ? 1 : 0;
  return Ci(i.map((n) => {
    let r = [];
    const s = t ? n.length() : n.length() - 1;
    for (let o = 0; o < s; o++)
      r.push(Bp(n.substrs[o] || "", e));
    return qs(r);
  }));
}, Rp = (i, t) => {
  for (const e of t) {
    if (e.start != i.start || e.end != i.end || e.substrs.join("") !== i.substrs.join(""))
      continue;
    let n = i.parts;
    const r = (o) => {
      for (const a of n) {
        if (a.start === o.start && a.substr === o.substr)
          return !1;
        if (!(o.length == 1 || a.length == 1) && (o.start < a.start && o.end > a.start || a.start < o.start && a.end > o.start))
          return !0;
      }
      return !1;
    };
    if (!(e.parts.filter(r).length > 0))
      return !0;
  }
  return !1;
};
class mi {
  constructor() {
    f(this, "parts");
    f(this, "substrs");
    f(this, "start");
    f(this, "end");
    this.parts = [], this.substrs = [], this.start = 0, this.end = 0;
  }
  add(t) {
    t && (this.parts.push(t), this.substrs.push(t.substr), this.start = Math.min(t.start, this.start), this.end = Math.max(t.end, this.end));
  }
  last() {
    return this.parts[this.parts.length - 1];
  }
  length() {
    return this.parts.length;
  }
  clone(t, e) {
    let n = new mi(), r = JSON.parse(JSON.stringify(this.parts)), s = r.pop();
    for (const c of r)
      n.add(c);
    let o = e.substr.substring(0, t - s.start), a = o.length;
    return n.add({ start: s.start, end: s.start + a, length: a, substr: o }), n;
  }
}
const Hp = (i) => {
  Op(), i = gi(i);
  let t = "", e = [new mi()];
  for (let n = 0; n < i.length; n++) {
    let s = i.substring(n).match(js);
    const o = i.substring(n, n + 1), a = s ? s[0] : null;
    let c = [], l = /* @__PURE__ */ new Set();
    for (const h of e) {
      const d = h.last();
      if (!d || d.length == 1 || d.end <= n)
        if (a) {
          const u = a.length;
          h.add({ start: n, end: n + u, length: u, substr: a }), l.add("1");
        } else
          h.add({ start: n, end: n + 1, length: 1, substr: o }), l.add("2");
      else if (a) {
        let u = h.clone(n, d);
        const p = a.length;
        u.add({ start: n, end: n + p, length: p, substr: a }), c.push(u);
      } else
        l.add("3");
    }
    if (c.length > 0) {
      c = c.sort((h, d) => h.length() - d.length());
      for (let h of c)
        Rp(h, e) || e.push(h);
      continue;
    }
    if (n > 0 && l.size == 1 && !l.has("3")) {
      t += Pr(e, !1);
      let h = new mi();
      const d = e[0];
      d && h.add(d.last()), e = [h];
    }
  }
  return t += Pr(e, !0), t;
}, $p = (i, t) => {
  if (i)
    return i[t];
}, Gp = (i, t) => {
  if (i) {
    for (var e, n = t.split("."); (e = n.shift()) && (i = i[e]); )
      ;
    return i;
  }
}, Ki = (i, t, e) => {
  var n, r;
  return !i || (i = i + "", t.regex == null) || (r = i.search(t.regex), r === -1) ? 0 : (n = t.string.length / i.length, r === 0 && (n += 0.5), n * e);
}, Zi = (i, t) => {
  var e = i[t];
  if (typeof e == "function")
    return e;
  e && !Array.isArray(e) && (i[t] = [e]);
}, Ve = (i, t) => {
  if (Array.isArray(i))
    i.forEach(t);
  else
    for (var e in i)
      i.hasOwnProperty(e) && t(i[e], e);
}, qp = (i, t) => typeof i == "number" && typeof t == "number" ? i > t ? 1 : i < t ? -1 : 0 : (i = gi(i + "").toLowerCase(), t = gi(t + "").toLowerCase(), i > t ? 1 : t > i ? -1 : 0);
class Vp {
  /**
   * Textually searches arrays and hashes of objects
   * by property (or multiple properties). Designed
   * specifically for autocomplete.
   *
   */
  constructor(t, e) {
    f(this, "items");
    // []|{};
    f(this, "settings");
    this.items = t, this.settings = e || { diacritics: !0 };
  }
  /**
   * Splits a search string into an array of individual
   * regexps to be used to match results.
   *
   */
  tokenize(t, e, n) {
    if (!t || !t.length)
      return [];
    const r = [], s = t.split(/\s+/);
    var o;
    return n && (o = new RegExp("^(" + Object.keys(n).map(ke).join("|") + "):(.*)$")), s.forEach((a) => {
      let c, l = null, h = null;
      o && (c = a.match(o)) && (l = c[1], a = c[2]), a.length > 0 && (this.settings.diacritics ? h = Hp(a) || null : h = ke(a), h && e && (h = "\\b" + h)), r.push({
        string: a,
        regex: h ? new RegExp(h, "iu") : null,
        field: l
      });
    }), r;
  }
  /**
   * Returns a function to be used to score individual results.
   *
   * Good matches will have a higher score than poor matches.
   * If an item is not a match, 0 will be returned by the function.
   *
   * @returns {T.ScoreFn}
   */
  getScoreFunction(t, e) {
    var n = this.prepareSearch(t, e);
    return this._getScoreFunction(n);
  }
  /**
   * @returns {T.ScoreFn}
   *
   */
  _getScoreFunction(t) {
    const e = t.tokens, n = e.length;
    if (!n)
      return function() {
        return 0;
      };
    const r = t.options.fields, s = t.weights, o = r.length, a = t.getAttrFn;
    if (!o)
      return function() {
        return 1;
      };
    const c = /* @__PURE__ */ (function() {
      return o === 1 ? function(l, h) {
        const d = r[0].field;
        return Ki(a(h, d), l, s[d] || 1);
      } : function(l, h) {
        var d = 0;
        if (l.field) {
          const u = a(h, l.field);
          !l.regex && u ? d += 1 / o : d += Ki(u, l, 1);
        } else
          Ve(s, (u, p) => {
            d += Ki(a(h, p), l, u);
          });
        return d / o;
      };
    })();
    return n === 1 ? function(l) {
      return c(e[0], l);
    } : t.options.conjunction === "and" ? function(l) {
      var h, d = 0;
      for (let u of e) {
        if (h = c(u, l), h <= 0)
          return 0;
        d += h;
      }
      return d / n;
    } : function(l) {
      var h = 0;
      return Ve(e, (d) => {
        h += c(d, l);
      }), h / n;
    };
  }
  /**
   * Returns a function that can be used to compare two
   * results, for sorting purposes. If no sorting should
   * be performed, `null` will be returned.
   *
   * @return function(a,b)
   */
  getSortFunction(t, e) {
    var n = this.prepareSearch(t, e);
    return this._getSortFunction(n);
  }
  _getSortFunction(t) {
    var e, n = [];
    const r = this, s = t.options, o = !t.query && s.sort_empty ? s.sort_empty : s.sort;
    if (typeof o == "function")
      return o.bind(this);
    const a = function(l, h) {
      return l === "$score" ? h.score : t.getAttrFn(r.items[h.id], l);
    };
    if (o)
      for (let l of o)
        (t.query || l.field !== "$score") && n.push(l);
    if (t.query) {
      e = !0;
      for (let l of n)
        if (l.field === "$score") {
          e = !1;
          break;
        }
      e && n.unshift({ field: "$score", direction: "desc" });
    } else
      n = n.filter((l) => l.field !== "$score");
    return n.length ? function(l, h) {
      var d, u;
      for (let p of n)
        if (u = p.field, d = (p.direction === "desc" ? -1 : 1) * qp(a(u, l), a(u, h)), d)
          return d;
      return 0;
    } : null;
  }
  /**
   * Parses a search query and returns an object
   * with tokens and fields ready to be populated
   * with results.
   *
   */
  prepareSearch(t, e) {
    const n = {};
    var r = Object.assign({}, e);
    if (Zi(r, "sort"), Zi(r, "sort_empty"), r.fields) {
      Zi(r, "fields");
      const s = [];
      r.fields.forEach((o) => {
        typeof o == "string" && (o = { field: o, weight: 1 }), s.push(o), n[o.field] = "weight" in o ? o.weight : 1;
      }), r.fields = s;
    }
    return {
      options: r,
      query: t.toLowerCase().trim(),
      tokens: this.tokenize(t, r.respect_word_boundaries, n),
      total: 0,
      items: [],
      weights: n,
      getAttrFn: r.nesting ? Gp : $p
    };
  }
  /**
   * Searches through all items and returns a sorted array of matches.
   *
   */
  search(t, e) {
    var n = this, r, s;
    s = this.prepareSearch(t, e), e = s.options, t = s.query;
    const o = e.score || n._getScoreFunction(s);
    t.length ? Ve(n.items, (c, l) => {
      r = o(c), (e.filter === !1 || r > 0) && s.items.push({ score: r, id: l });
    }) : Ve(n.items, (c, l) => {
      s.items.push({ score: 1, id: l });
    });
    const a = n._getSortFunction(s);
    return a && s.items.sort(a), s.total = s.items.length, typeof e.limit == "number" && (s.items = s.items.slice(0, e.limit)), s;
  }
}
const Ct = (i) => typeof i > "u" || i === null ? null : ii(i), ii = (i) => typeof i == "boolean" ? i ? "1" : "0" : i + "", Qi = (i) => (i + "").replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;"), Up = (i, t) => t > 0 ? window.setTimeout(i, t) : (i.call(null), null), jp = (i, t) => {
  var e;
  return function(n, r) {
    var s = this;
    e && (s.loading = Math.max(s.loading - 1, 0), clearTimeout(e)), e = setTimeout(function() {
      e = null, s.loadedSearches[n] = !0, i.call(s, n, r);
    }, t);
  };
}, Dr = (i, t, e) => {
  var n, r = i.trigger, s = {};
  i.trigger = function() {
    var o = arguments[0];
    if (t.indexOf(o) !== -1)
      s[o] = arguments;
    else
      return r.apply(i, arguments);
  }, e.apply(i, []), i.trigger = r;
  for (n of t)
    n in s && r.apply(i, s[n]);
}, Yp = (i) => ({
  start: i.selectionStart || 0,
  length: (i.selectionEnd || 0) - (i.selectionStart || 0)
}), J = (i, t = !1) => {
  i && (i.preventDefault(), t && i.stopPropagation());
}, ht = (i, t, e, n) => {
  i.addEventListener(t, e, n);
}, Ut = (i, t) => {
  if (!t || !t[i])
    return !1;
  var e = (t.altKey ? 1 : 0) + (t.ctrlKey ? 1 : 0) + (t.shiftKey ? 1 : 0) + (t.metaKey ? 1 : 0);
  return e === 1;
}, Ji = (i, t) => {
  const e = i.getAttribute("id");
  return e || (i.setAttribute("id", t), t);
}, Fr = (i) => i.replace(/[\\"']/g, "\\$&"), jt = (i, t) => {
  t && i.append(t);
}, rt = (i, t) => {
  if (Array.isArray(i))
    i.forEach(t);
  else
    for (var e in i)
      i.hasOwnProperty(e) && t(i[e], e);
}, Nt = (i) => {
  if (i.jquery)
    return i[0];
  if (i instanceof HTMLElement)
    return i;
  if (Ys(i)) {
    var t = document.createElement("template");
    return t.innerHTML = i.trim(), t.content.firstChild;
  }
  return document.querySelector(i);
}, Ys = (i) => typeof i == "string" && i.indexOf("<") > -1, Xp = (i) => i.replace(/['"\\]/g, "\\$&"), tn = (i, t) => {
  var e = document.createEvent("HTMLEvents");
  e.initEvent(t, !0, !1), i.dispatchEvent(e);
}, Ue = (i, t) => {
  Object.assign(i.style, t);
}, yt = (i, ...t) => {
  var e = Xs(t);
  i = Ws(i), i.map((n) => {
    e.map((r) => {
      n.classList.add(r);
    });
  });
}, Bt = (i, ...t) => {
  var e = Xs(t);
  i = Ws(i), i.map((n) => {
    e.map((r) => {
      n.classList.remove(r);
    });
  });
}, Xs = (i) => {
  var t = [];
  return rt(i, (e) => {
    typeof e == "string" && (e = e.trim().split(/[\t\n\f\r\s]/)), Array.isArray(e) && (t = t.concat(e));
  }), t.filter(Boolean);
}, Ws = (i) => (Array.isArray(i) || (i = [i]), i), en = (i, t, e) => {
  if (!(e && !e.contains(i)))
    for (; i && i.matches; ) {
      if (i.matches(t))
        return i;
      i = i.parentNode;
    }
}, zr = (i, t = 0) => t > 0 ? i[i.length - 1] : i[0], Wp = (i) => Object.keys(i).length === 0, Br = (i, t) => {
  if (!i)
    return -1;
  t = t || i.nodeName;
  for (var e = 0; i = i.previousElementSibling; )
    i.matches(t) && e++;
  return e;
}, K = (i, t) => {
  rt(t, (e, n) => {
    e == null ? i.removeAttribute(n) : i.setAttribute(n, "" + e);
  });
}, xn = (i, t) => {
  i.parentNode && i.parentNode.replaceChild(t, i);
}, Kp = (i, t) => {
  if (t === null)
    return;
  if (typeof t == "string") {
    if (!t.length)
      return;
    t = new RegExp(t, "i");
  }
  const e = (s) => {
    var o = s.data.match(t);
    if (o && s.data.length > 0) {
      var a = document.createElement("span");
      a.className = "highlight";
      var c = s.splitText(o.index);
      c.splitText(o[0].length);
      var l = c.cloneNode(!0);
      return a.appendChild(l), xn(c, a), 1;
    }
    return 0;
  }, n = (s) => {
    s.nodeType === 1 && s.childNodes && !/(script|style)/i.test(s.tagName) && (s.className !== "highlight" || s.tagName !== "SPAN") && Array.from(s.childNodes).forEach((o) => {
      r(o);
    });
  }, r = (s) => s.nodeType === 3 ? e(s) : (n(s), 0);
  r(i);
}, Zp = (i) => {
  var t = i.querySelectorAll("span.highlight");
  Array.prototype.forEach.call(t, function(e) {
    var n = e.parentNode;
    n.replaceChild(e.firstChild, e), n.normalize();
  });
}, Qp = 65, Jp = 13, tf = 27, ef = 37, nf = 38, rf = 39, sf = 40, Rr = 8, of = 46, Hr = 9, af = typeof navigator > "u" ? !1 : /Mac/.test(navigator.userAgent), je = af ? "metaKey" : "ctrlKey", $r = {
  options: [],
  optgroups: [],
  plugins: [],
  delimiter: ",",
  splitOn: null,
  // regexp or string for splitting up values from a paste command
  persist: !0,
  diacritics: !0,
  create: null,
  createOnBlur: !1,
  createFilter: null,
  highlight: !0,
  openOnFocus: !0,
  shouldOpen: null,
  maxOptions: 50,
  maxItems: null,
  hideSelected: null,
  duplicates: !1,
  addPrecedence: !1,
  selectOnTab: !1,
  preload: null,
  allowEmptyOption: !1,
  //closeAfterSelect: false,
  refreshThrottle: 300,
  loadThrottle: 300,
  loadingClass: "loading",
  dataAttr: null,
  //'data-data',
  optgroupField: "optgroup",
  valueField: "value",
  labelField: "text",
  disabledField: "disabled",
  optgroupLabelField: "label",
  optgroupValueField: "value",
  lockOptgroupOrder: !1,
  sortField: "$order",
  searchField: ["text"],
  searchConjunction: "and",
  mode: null,
  wrapperClass: "ts-wrapper",
  controlClass: "ts-control",
  dropdownClass: "ts-dropdown",
  dropdownContentClass: "ts-dropdown-content",
  itemClass: "item",
  optionClass: "option",
  dropdownParent: null,
  controlInput: '<input type="text" autocomplete="off" size="1" />',
  copyClassesToDropdown: !1,
  placeholder: null,
  hidePlaceholder: null,
  shouldLoad: function(i) {
    return i.length > 0;
  },
  /*
  load                 : null, // function(query, callback) { ... }
  score                : null, // function(search) { ... }
  onInitialize         : null, // function() { ... }
  onChange             : null, // function(value) { ... }
  onItemAdd            : null, // function(value, $item) { ... }
  onItemRemove         : null, // function(value) { ... }
  onClear              : null, // function() { ... }
  onOptionAdd          : null, // function(value, data) { ... }
  onOptionRemove       : null, // function(value) { ... }
  onOptionClear        : null, // function() { ... }
  onOptionGroupAdd     : null, // function(id, data) { ... }
  onOptionGroupRemove  : null, // function(id) { ... }
  onOptionGroupClear   : null, // function() { ... }
  onDropdownOpen       : null, // function(dropdown) { ... }
  onDropdownClose      : null, // function(dropdown) { ... }
  onType               : null, // function(str) { ... }
  onDelete             : null, // function(values) { ... }
  */
  render: {
    /*
    item: null,
    optgroup: null,
    optgroup_header: null,
    option: null,
    option_create: null
    */
  }
};
function Gr(i, t) {
  var e = Object.assign({}, $r, t), n = e.dataAttr, r = e.labelField, s = e.valueField, o = e.disabledField, a = e.optgroupField, c = e.optgroupLabelField, l = e.optgroupValueField, h = i.tagName.toLowerCase(), d = i.getAttribute("placeholder") || i.getAttribute("data-placeholder");
  if (!d && !e.allowEmptyOption) {
    let v = i.querySelector('option[value=""]');
    v && (d = v.textContent);
  }
  var u = {
    placeholder: d,
    options: [],
    optgroups: [],
    items: [],
    maxItems: null
  }, p = () => {
    var v, y = u.options, b = {}, x = 1;
    let S = 0;
    var C = (k) => {
      var A = Object.assign({}, k.dataset), I = n && A[n];
      return typeof I == "string" && I.length && (A = Object.assign(A, JSON.parse(I))), A;
    }, N = (k, A) => {
      var I = Ct(k.value);
      if (I != null && !(!I && !e.allowEmptyOption)) {
        if (b.hasOwnProperty(I)) {
          if (A) {
            var z = b[I][a];
            z ? Array.isArray(z) ? z.push(A) : b[I][a] = [z, A] : b[I][a] = A;
          }
        } else {
          var F = C(k);
          F[r] = F[r] || k.textContent, F[s] = F[s] || I, F[o] = F[o] || k.disabled, F[a] = F[a] || A, F.$option = k, F.$order = F.$order || ++S, b[I] = F, y.push(F);
        }
        k.selected && u.items.push(I);
      }
    }, P = (k) => {
      var A, I;
      I = C(k), I[c] = I[c] || k.getAttribute("label") || "", I[l] = I[l] || x++, I[o] = I[o] || k.disabled, I.$order = I.$order || ++S, u.optgroups.push(I), A = I[l], rt(k.children, (z) => {
        N(z, A);
      });
    };
    u.maxItems = i.hasAttribute("multiple") ? null : 1, rt(i.children, (k) => {
      v = k.tagName.toLowerCase(), v === "optgroup" ? P(k) : v === "option" && N(k);
    });
  }, g = () => {
    const v = i.getAttribute(n);
    if (v)
      u.options = JSON.parse(v), rt(u.options, (b) => {
        u.items.push(b[s]);
      });
    else {
      var y = i.value.trim() || "";
      if (!e.allowEmptyOption && !y.length)
        return;
      const b = y.split(e.delimiter);
      rt(b, (x) => {
        const S = {};
        S[r] = x, S[s] = x, u.options.push(S);
      }), u.items = b;
    }
  };
  return h === "select" ? p() : g(), Object.assign({}, $r, u, t);
}
var qr = 0;
class at extends Ep(Mp) {
  constructor(t, e) {
    super(), this.order = 0, this.isOpen = !1, this.isDisabled = !1, this.isReadOnly = !1, this.isInvalid = !1, this.isValid = !0, this.isLocked = !1, this.isFocused = !1, this.isInputHidden = !1, this.isSetup = !1, this.ignoreFocus = !1, this.ignoreHover = !1, this.hasOptions = !1, this.lastValue = "", this.caretPos = 0, this.loading = 0, this.loadedSearches = {}, this.activeOption = null, this.activeItems = [], this.optgroups = {}, this.options = {}, this.userOptions = {}, this.items = [], this.refreshTimeout = null, qr++;
    var n, r = Nt(t);
    if (r.tomselect)
      throw new Error("Tom Select already initialized on this element");
    r.tomselect = this;
    var s = window.getComputedStyle && window.getComputedStyle(r, null);
    n = s.getPropertyValue("direction");
    const o = Gr(r, e);
    this.settings = o, this.input = r, this.tabIndex = r.tabIndex || 0, this.is_select_tag = r.tagName.toLowerCase() === "select", this.rtl = /rtl/i.test(n), this.inputId = Ji(r, "tomselect-" + qr), this.isRequired = r.required, this.sifter = new Vp(this.options, { diacritics: o.diacritics }), o.mode = o.mode || (o.maxItems === 1 ? "single" : "multi"), typeof o.hideSelected != "boolean" && (o.hideSelected = o.mode === "multi"), typeof o.hidePlaceholder != "boolean" && (o.hidePlaceholder = o.mode !== "multi");
    var a = o.createFilter;
    typeof a != "function" && (typeof a == "string" && (a = new RegExp(a)), a instanceof RegExp ? o.createFilter = (y) => a.test(y) : o.createFilter = (y) => this.settings.duplicates || !this.options[y]), this.initializePlugins(o.plugins), this.setupCallbacks(), this.setupTemplates();
    const c = Nt("<div>"), l = Nt("<div>"), h = this._render("dropdown"), d = Nt('<div role="listbox" tabindex="-1">'), u = this.input.getAttribute("class") || "", p = o.mode;
    var g;
    if (yt(c, o.wrapperClass, u, p), yt(l, o.controlClass), jt(c, l), yt(h, o.dropdownClass, p), o.copyClassesToDropdown && yt(h, u), yt(d, o.dropdownContentClass), jt(h, d), Nt(o.dropdownParent || c).appendChild(h), Ys(o.controlInput)) {
      g = Nt(o.controlInput);
      var v = ["autocorrect", "autocapitalize", "autocomplete", "spellcheck"];
      rt(v, (y) => {
        r.getAttribute(y) && K(g, { [y]: r.getAttribute(y) });
      }), g.tabIndex = -1, l.appendChild(g), this.focus_node = g;
    } else o.controlInput ? (g = Nt(o.controlInput), this.focus_node = g) : (g = Nt("<input/>"), this.focus_node = l);
    this.wrapper = c, this.dropdown = h, this.dropdown_content = d, this.control = l, this.control_input = g, this.setup();
  }
  /**
   * set up event bindings.
   *
   */
  setup() {
    const t = this, e = t.settings, n = t.control_input, r = t.dropdown, s = t.dropdown_content, o = t.wrapper, a = t.control, c = t.input, l = t.focus_node, h = { passive: !0 }, d = t.inputId + "-ts-dropdown";
    K(s, {
      id: d
    }), K(l, {
      role: "combobox",
      "aria-haspopup": "listbox",
      "aria-expanded": "false",
      "aria-controls": d
    });
    const u = Ji(l, t.inputId + "-ts-control"), p = "label[for='" + Xp(t.inputId) + "']", g = document.querySelector(p), v = t.focus.bind(t);
    if (g) {
      ht(g, "click", v), K(g, { for: u });
      const x = Ji(g, t.inputId + "-ts-label");
      K(l, { "aria-labelledby": x }), K(s, { "aria-labelledby": x });
    }
    if (o.style.width = c.style.width, t.plugins.names.length) {
      const x = "plugin-" + t.plugins.names.join(" plugin-");
      yt([o, r], x);
    }
    (e.maxItems === null || e.maxItems > 1) && t.is_select_tag && K(c, { multiple: "multiple" }), e.placeholder && K(n, { placeholder: e.placeholder }), !e.splitOn && e.delimiter && (e.splitOn = new RegExp("\\s*" + ke(e.delimiter) + "+\\s*")), e.load && e.loadThrottle && (e.load = jp(e.load, e.loadThrottle)), ht(r, "mousemove", () => {
      t.ignoreHover = !1;
    }), ht(r, "mouseenter", (x) => {
      var S = en(x.target, "[data-selectable]", r);
      S && t.onOptionHover(x, S);
    }, { capture: !0 }), ht(r, "click", (x) => {
      const S = en(x.target, "[data-selectable]");
      S && (t.onOptionSelect(x, S), J(x, !0));
    }), ht(a, "click", (x) => {
      var S = en(x.target, "[data-ts-item]", a);
      if (S && t.onItemSelect(x, S)) {
        J(x, !0);
        return;
      }
      n.value == "" && (t.onClick(), J(x, !0));
    }), ht(l, "keydown", (x) => t.onKeyDown(x)), ht(n, "keypress", (x) => t.onKeyPress(x)), ht(n, "input", (x) => t.onInput(x)), ht(l, "blur", (x) => t.onBlur(x)), ht(l, "focus", (x) => t.onFocus(x)), ht(n, "paste", (x) => t.onPaste(x));
    const y = (x) => {
      const S = x.composedPath()[0];
      if (!o.contains(S) && !r.contains(S)) {
        t.isFocused && t.blur(), t.inputState();
        return;
      }
      S == n && t.isOpen ? x.stopPropagation() : J(x, !0);
    }, b = () => {
      t.isOpen && t.positionDropdown();
    };
    ht(document, "mousedown", y), ht(window, "scroll", b, h), ht(window, "resize", b, h), this._destroy = () => {
      document.removeEventListener("mousedown", y), window.removeEventListener("scroll", b), window.removeEventListener("resize", b), g && g.removeEventListener("click", v);
    }, this.revertSettings = {
      innerHTML: c.innerHTML,
      tabIndex: c.tabIndex
    }, c.tabIndex = -1, c.insertAdjacentElement("afterend", t.wrapper), t.sync(!1), e.items = [], delete e.optgroups, delete e.options, ht(c, "invalid", () => {
      t.isValid && (t.isValid = !1, t.isInvalid = !0, t.refreshState());
    }), t.updateOriginalInput(), t.refreshItems(), t.close(!1), t.inputState(), t.isSetup = !0, c.disabled ? t.disable() : c.readOnly ? t.setReadOnly(!0) : t.enable(), t.on("change", this.onChange), yt(c, "tomselected", "ts-hidden-accessible"), t.trigger("initialize"), e.preload === !0 && t.preload();
  }
  /**
   * Register options and optgroups
   *
   */
  setupOptions(t = [], e = []) {
    this.addOptions(t), rt(e, (n) => {
      this.registerOptionGroup(n);
    });
  }
  /**
   * Sets up default rendering functions.
   */
  setupTemplates() {
    var t = this, e = t.settings.labelField, n = t.settings.optgroupLabelField, r = {
      optgroup: (s) => {
        let o = document.createElement("div");
        return o.className = "optgroup", o.appendChild(s.options), o;
      },
      optgroup_header: (s, o) => '<div class="optgroup-header">' + o(s[n]) + "</div>",
      option: (s, o) => "<div>" + o(s[e]) + "</div>",
      item: (s, o) => "<div>" + o(s[e]) + "</div>",
      option_create: (s, o) => '<div class="create">Add <strong>' + o(s.input) + "</strong>&hellip;</div>",
      no_results: () => '<div class="no-results">No results found</div>',
      loading: () => '<div class="spinner"></div>',
      not_loading: () => {
      },
      dropdown: () => "<div></div>"
    };
    t.settings.render = Object.assign({}, r, t.settings.render);
  }
  /**
   * Maps fired events to callbacks provided
   * in the settings used when creating the control.
   */
  setupCallbacks() {
    var t, e, n = {
      initialize: "onInitialize",
      change: "onChange",
      item_add: "onItemAdd",
      item_remove: "onItemRemove",
      item_select: "onItemSelect",
      clear: "onClear",
      option_add: "onOptionAdd",
      option_remove: "onOptionRemove",
      option_clear: "onOptionClear",
      optgroup_add: "onOptionGroupAdd",
      optgroup_remove: "onOptionGroupRemove",
      optgroup_clear: "onOptionGroupClear",
      dropdown_open: "onDropdownOpen",
      dropdown_close: "onDropdownClose",
      type: "onType",
      load: "onLoad",
      focus: "onFocus",
      blur: "onBlur"
    };
    for (t in n)
      e = this.settings[n[t]], e && this.on(t, e);
  }
  /**
   * Sync the Tom Select instance with the original input or select
   *
   */
  sync(t = !0) {
    const e = this, n = t ? Gr(e.input, { delimiter: e.settings.delimiter }) : e.settings;
    e.setupOptions(n.options, n.optgroups), e.setValue(n.items || [], !0), e.lastQuery = null;
  }
  /**
   * Triggered when the main control element
   * has a click event.
   *
   */
  onClick() {
    var t = this;
    if (t.activeItems.length > 0) {
      t.clearActiveItems(), t.focus();
      return;
    }
    t.isFocused && t.isOpen ? t.blur() : t.focus();
  }
  /**
   * @deprecated v1.7
   *
   */
  onMouseDown() {
  }
  /**
   * Triggered when the value of the control has been changed.
   * This should propagate the event to the original DOM
   * input / select element.
   */
  onChange() {
    tn(this.input, "input"), tn(this.input, "change");
  }
  /**
   * Triggered on <input> paste.
   *
   */
  onPaste(t) {
    var e = this;
    if (e.isInputHidden || e.isLocked) {
      J(t);
      return;
    }
    e.settings.splitOn && setTimeout(() => {
      var n = e.inputValue();
      if (n.match(e.settings.splitOn)) {
        var r = n.trim().split(e.settings.splitOn);
        rt(r, (s) => {
          Ct(s) && (this.options[s] ? e.addItem(s) : e.createItem(s));
        });
      }
    }, 0);
  }
  /**
   * Triggered on <input> keypress.
   *
   */
  onKeyPress(t) {
    var e = this;
    if (e.isLocked) {
      J(t);
      return;
    }
    var n = String.fromCharCode(t.keyCode || t.which);
    if (e.settings.create && e.settings.mode === "multi" && n === e.settings.delimiter) {
      e.createItem(), J(t);
      return;
    }
  }
  /**
   * Triggered on <input> keydown.
   *
   */
  onKeyDown(t) {
    var e = this;
    if (e.ignoreHover = !0, e.isLocked) {
      t.keyCode !== Hr && J(t);
      return;
    }
    switch (t.keyCode) {
      // ctrl+A: select all
      case Qp:
        if (Ut(je, t) && e.control_input.value == "") {
          J(t), e.selectAll();
          return;
        }
        break;
      // esc: close dropdown
      case tf:
        e.isOpen && (J(t, !0), e.close()), e.clearActiveItems();
        return;
      // down: open dropdown or move selection down
      case sf:
        if (!e.isOpen && e.hasOptions)
          e.open();
        else if (e.activeOption) {
          let n = e.getAdjacent(e.activeOption, 1);
          n && e.setActiveOption(n);
        }
        J(t);
        return;
      // up: move selection up
      case nf:
        if (e.activeOption) {
          let n = e.getAdjacent(e.activeOption, -1);
          n && e.setActiveOption(n);
        }
        J(t);
        return;
      // return: select active option
      case Jp:
        e.canSelect(e.activeOption) ? (e.onOptionSelect(t, e.activeOption), J(t)) : (e.settings.create && e.createItem() || document.activeElement == e.control_input && e.isOpen) && J(t);
        return;
      // left: modifiy item selection to the left
      case ef:
        e.advanceSelection(-1, t);
        return;
      // right: modifiy item selection to the right
      case rf:
        e.advanceSelection(1, t);
        return;
      // tab: select active option and/or create item
      case Hr:
        e.settings.selectOnTab && (e.canSelect(e.activeOption) && (e.onOptionSelect(t, e.activeOption), J(t)), e.settings.create && e.createItem() && J(t));
        return;
      // delete|backspace: delete items
      case Rr:
      case of:
        e.deleteSelection(t);
        return;
    }
    e.isInputHidden && !Ut(je, t) && J(t);
  }
  /**
   * Triggered on <input> keyup.
   *
   */
  onInput(t) {
    if (this.isLocked)
      return;
    const e = this.inputValue();
    if (this.lastValue !== e) {
      if (this.lastValue = e, e == "") {
        this._onInput();
        return;
      }
      this.refreshTimeout && window.clearTimeout(this.refreshTimeout), this.refreshTimeout = Up(() => {
        this.refreshTimeout = null, this._onInput();
      }, this.settings.refreshThrottle);
    }
  }
  _onInput() {
    const t = this.lastValue;
    this.settings.shouldLoad.call(this, t) && this.load(t), this.refreshOptions(), this.trigger("type", t);
  }
  /**
   * Triggered when the user rolls over
   * an option in the autocomplete dropdown menu.
   *
   */
  onOptionHover(t, e) {
    this.ignoreHover || this.setActiveOption(e, !1);
  }
  /**
   * Triggered on <input> focus.
   *
   */
  onFocus(t) {
    var e = this, n = e.isFocused;
    if (e.isDisabled || e.isReadOnly) {
      e.blur(), J(t);
      return;
    }
    e.ignoreFocus || (e.isFocused = !0, e.settings.preload === "focus" && e.preload(), n || e.trigger("focus"), e.activeItems.length || (e.inputState(), e.refreshOptions(!!e.settings.openOnFocus)), e.refreshState());
  }
  /**
   * Triggered on <input> blur.
   *
   */
  onBlur(t) {
    if (document.hasFocus() !== !1) {
      var e = this;
      if (e.isFocused) {
        e.isFocused = !1, e.ignoreFocus = !1;
        var n = () => {
          e.close(), e.setActiveItem(), e.setCaret(e.items.length), e.trigger("blur");
        };
        e.settings.create && e.settings.createOnBlur ? e.createItem(null, n) : n();
      }
    }
  }
  /**
   * Triggered when the user clicks on an option
   * in the autocomplete dropdown menu.
   *
   */
  onOptionSelect(t, e) {
    var n, r = this;
    e.parentElement && e.parentElement.matches("[data-disabled]") || (e.classList.contains("create") ? r.createItem(null, () => {
      r.settings.closeAfterSelect && r.close();
    }) : (n = e.dataset.value, typeof n < "u" && (r.lastQuery = null, r.addItem(n), r.settings.closeAfterSelect && r.close(), !r.settings.hideSelected && t.type && /click/.test(t.type) && r.setActiveOption(e))));
  }
  /**
   * Return true if the given option can be selected
   *
   */
  canSelect(t) {
    return !!(this.isOpen && t && this.dropdown_content.contains(t));
  }
  /**
   * Triggered when the user clicks on an item
   * that has been selected.
   *
   */
  onItemSelect(t, e) {
    var n = this;
    return !n.isLocked && n.settings.mode === "multi" ? (J(t), n.setActiveItem(e, t), !0) : !1;
  }
  /**
   * Determines whether or not to invoke
   * the user-provided option provider / loader
   *
   * Note, there is a subtle difference between
   * this.canLoad() and this.settings.shouldLoad();
   *
   *	- settings.shouldLoad() is a user-input validator.
   *	When false is returned, the not_loading template
   *	will be added to the dropdown
   *
   *	- canLoad() is lower level validator that checks
   * 	the Tom Select instance. There is no inherent user
   *	feedback when canLoad returns false
   *
   */
  canLoad(t) {
    return !(!this.settings.load || this.loadedSearches.hasOwnProperty(t));
  }
  /**
   * Invokes the user-provided option provider / loader.
   *
   */
  load(t) {
    const e = this;
    if (!e.canLoad(t))
      return;
    yt(e.wrapper, e.settings.loadingClass), e.loading++;
    const n = e.loadCallback.bind(e);
    e.settings.load.call(e, t, n);
  }
  /**
   * Invoked by the user-provided option provider
   *
   */
  loadCallback(t, e) {
    const n = this;
    n.loading = Math.max(n.loading - 1, 0), n.lastQuery = null, n.clearActiveOption(), n.setupOptions(t, e), n.refreshOptions(n.isFocused && !n.isInputHidden), n.loading || Bt(n.wrapper, n.settings.loadingClass), n.trigger("load", t, e);
  }
  preload() {
    var t = this.wrapper.classList;
    t.contains("preloaded") || (t.add("preloaded"), this.load(""));
  }
  /**
   * Sets the input field of the control to the specified value.
   *
   */
  setTextboxValue(t = "") {
    var e = this.control_input, n = e.value !== t;
    n && (e.value = t, tn(e, "update"), this.lastValue = t);
  }
  /**
   * Returns the value of the control. If multiple items
   * can be selected (e.g. <select multiple>), this returns
   * an array. If only one item can be selected, this
   * returns a string.
   *
   */
  getValue() {
    return this.is_select_tag && this.input.hasAttribute("multiple") ? this.items : this.items.join(this.settings.delimiter);
  }
  /**
   * Resets the selected items to the given value.
   *
   */
  setValue(t, e) {
    var n = e ? [] : ["change"];
    Dr(this, n, () => {
      this.clear(e), this.addItems(t, e);
    });
  }
  /**
   * Resets the number of max items to the given value
   *
   */
  setMaxItems(t) {
    t === 0 && (t = null), this.settings.maxItems = t, this.refreshState();
  }
  /**
   * Sets the selected item.
   *
   */
  setActiveItem(t, e) {
    var n = this, r, s, o, a, c, l;
    if (n.settings.mode !== "single") {
      if (!t) {
        n.clearActiveItems(), n.isFocused && n.inputState();
        return;
      }
      if (r = e && e.type.toLowerCase(), r === "click" && Ut("shiftKey", e) && n.activeItems.length) {
        for (l = n.getLastActive(), o = Array.prototype.indexOf.call(n.control.children, l), a = Array.prototype.indexOf.call(n.control.children, t), o > a && (c = o, o = a, a = c), s = o; s <= a; s++)
          t = n.control.children[s], n.activeItems.indexOf(t) === -1 && n.setActiveItemClass(t);
        J(e);
      } else r === "click" && Ut(je, e) || r === "keydown" && Ut("shiftKey", e) ? t.classList.contains("active") ? n.removeActiveItem(t) : n.setActiveItemClass(t) : (n.clearActiveItems(), n.setActiveItemClass(t));
      n.inputState(), n.isFocused || n.focus();
    }
  }
  /**
   * Set the active and last-active classes
   *
   */
  setActiveItemClass(t) {
    const e = this, n = e.control.querySelector(".last-active");
    n && Bt(n, "last-active"), yt(t, "active last-active"), e.trigger("item_select", t), e.activeItems.indexOf(t) == -1 && e.activeItems.push(t);
  }
  /**
   * Remove active item
   *
   */
  removeActiveItem(t) {
    var e = this.activeItems.indexOf(t);
    this.activeItems.splice(e, 1), Bt(t, "active");
  }
  /**
   * Clears all the active items
   *
   */
  clearActiveItems() {
    Bt(this.activeItems, "active"), this.activeItems = [];
  }
  /**
   * Sets the selected item in the dropdown menu
   * of available options.
   *
   */
  setActiveOption(t, e = !0) {
    t !== this.activeOption && (this.clearActiveOption(), t && (this.activeOption = t, K(this.focus_node, { "aria-activedescendant": t.getAttribute("id") }), K(t, { "aria-selected": "true" }), yt(t, "active"), e && this.scrollToOption(t)));
  }
  /**
   * Sets the dropdown_content scrollTop to display the option
   *
   */
  scrollToOption(t, e) {
    if (!t)
      return;
    const n = this.dropdown_content, r = n.clientHeight, s = n.scrollTop || 0, o = t.offsetHeight, a = t.getBoundingClientRect().top - n.getBoundingClientRect().top + s;
    a + o > r + s ? this.scroll(a - r + o, e) : a < s && this.scroll(a, e);
  }
  /**
   * Scroll the dropdown to the given position
   *
   */
  scroll(t, e) {
    const n = this.dropdown_content;
    e && (n.style.scrollBehavior = e), n.scrollTop = t, n.style.scrollBehavior = "";
  }
  /**
   * Clears the active option
   *
   */
  clearActiveOption() {
    this.activeOption && (Bt(this.activeOption, "active"), K(this.activeOption, { "aria-selected": null })), this.activeOption = null, K(this.focus_node, { "aria-activedescendant": null });
  }
  /**
   * Selects all items (CTRL + A).
   */
  selectAll() {
    const t = this;
    if (t.settings.mode === "single")
      return;
    const e = t.controlChildren();
    e.length && (t.inputState(), t.close(), t.activeItems = e, rt(e, (n) => {
      t.setActiveItemClass(n);
    }));
  }
  /**
   * Determines if the control_input should be in a hidden or visible state
   *
   */
  inputState() {
    var t = this;
    t.control.contains(t.control_input) && (K(t.control_input, { placeholder: t.settings.placeholder }), t.activeItems.length > 0 || !t.isFocused && t.settings.hidePlaceholder && t.items.length > 0 ? (t.setTextboxValue(), t.isInputHidden = !0) : (t.settings.hidePlaceholder && t.items.length > 0 && K(t.control_input, { placeholder: "" }), t.isInputHidden = !1), t.wrapper.classList.toggle("input-hidden", t.isInputHidden));
  }
  /**
   * Get the input value
   */
  inputValue() {
    return this.control_input.value.trim();
  }
  /**
   * Gives the control focus.
   */
  focus() {
    var t = this;
    t.isDisabled || t.isReadOnly || (t.ignoreFocus = !0, t.control_input.offsetWidth ? t.control_input.focus() : t.focus_node.focus(), setTimeout(() => {
      t.ignoreFocus = !1, t.onFocus();
    }, 0));
  }
  /**
   * Forces the control out of focus.
   *
   */
  blur() {
    this.focus_node.blur(), this.onBlur();
  }
  /**
   * Returns a function that scores an object
   * to show how good of a match it is to the
   * provided query.
   *
   * @return {function}
   */
  getScoreFunction(t) {
    return this.sifter.getScoreFunction(t, this.getSearchOptions());
  }
  /**
   * Returns search options for sifter (the system
   * for scoring and sorting results).
   *
   * @see https://github.com/orchidjs/sifter.js
   * @return {object}
   */
  getSearchOptions() {
    var t = this.settings, e = t.sortField;
    return typeof t.sortField == "string" && (e = [{ field: t.sortField }]), {
      fields: t.searchField,
      conjunction: t.searchConjunction,
      sort: e,
      nesting: t.nesting
    };
  }
  /**
   * Searches through available options and returns
   * a sorted array of matches.
   *
   */
  search(t) {
    var e, n, r = this, s = this.getSearchOptions();
    if (r.settings.score && (n = r.settings.score.call(r, t), typeof n != "function"))
      throw new Error('Tom Select "score" setting must be a function that returns a function');
    return t !== r.lastQuery ? (r.lastQuery = t, e = r.sifter.search(t, Object.assign(s, { score: n })), r.currentResults = e) : e = Object.assign({}, r.currentResults), r.settings.hideSelected && (e.items = e.items.filter((o) => {
      let a = Ct(o.id);
      return !(a && r.items.indexOf(a) !== -1);
    })), e;
  }
  /**
   * Refreshes the list of available options shown
   * in the autocomplete dropdown menu.
   *
   */
  refreshOptions(t = !0) {
    var e, n, r, s, o, a, c, l, h, d;
    const u = {}, p = [];
    var g = this, v = g.inputValue();
    const y = v === g.lastQuery || v == "" && g.lastQuery == null;
    var b = g.search(v), x = null, S = g.settings.shouldOpen || !1, C = g.dropdown_content;
    y && (x = g.activeOption, x && (h = x.closest("[data-group]"))), s = b.items.length, typeof g.settings.maxOptions == "number" && (s = Math.min(s, g.settings.maxOptions)), s > 0 && (S = !0);
    const N = (k, A) => {
      let I = u[k];
      if (I !== void 0) {
        let F = p[I];
        if (F !== void 0)
          return [I, F.fragment];
      }
      let z = document.createDocumentFragment();
      return I = p.length, p.push({ fragment: z, order: A, optgroup: k }), [I, z];
    };
    for (e = 0; e < s; e++) {
      let k = b.items[e];
      if (!k)
        continue;
      let A = k.id, I = g.options[A];
      if (I === void 0)
        continue;
      let z = ii(A), F = g.getOption(z, !0);
      for (g.settings.hideSelected || F.classList.toggle("selected", g.items.includes(z)), o = I[g.settings.optgroupField] || "", a = Array.isArray(o) ? o : [o], n = 0, r = a && a.length; n < r; n++) {
        o = a[n];
        let Z = I.$order, Q = g.optgroups[o];
        Q === void 0 ? o = "" : Z = Q.$order;
        const [E, L] = N(o, Z);
        n > 0 && (F = F.cloneNode(!0), K(F, { id: I.$id + "-clone-" + n, "aria-selected": null }), F.classList.add("ts-cloned"), Bt(F, "active"), g.activeOption && g.activeOption.dataset.value == A && h && h.dataset.group === o.toString() && (x = F)), L.appendChild(F), o != "" && (u[o] = E);
      }
    }
    g.settings.lockOptgroupOrder && p.sort((k, A) => k.order - A.order), c = document.createDocumentFragment(), rt(p, (k) => {
      let A = k.fragment, I = k.optgroup;
      if (!A || !A.children.length)
        return;
      let z = g.optgroups[I];
      if (z !== void 0) {
        let F = document.createDocumentFragment(), Z = g.render("optgroup_header", z);
        jt(F, Z), jt(F, A);
        let Q = g.render("optgroup", { group: z, options: F });
        jt(c, Q);
      } else
        jt(c, A);
    }), C.innerHTML = "", jt(C, c), g.settings.highlight && (Zp(C), b.query.length && b.tokens.length && rt(b.tokens, (k) => {
      Kp(C, k.regex);
    }));
    var P = (k) => {
      let A = g.render(k, { input: v });
      return A && (S = !0, C.insertBefore(A, C.firstChild)), A;
    };
    if (g.loading ? P("loading") : g.settings.shouldLoad.call(g, v) ? b.items.length === 0 && P("no_results") : P("not_loading"), l = g.canCreate(v), l && (d = P("option_create")), g.hasOptions = b.items.length > 0 || l, S) {
      if (b.items.length > 0) {
        if (!x && g.settings.mode === "single" && g.items[0] != null && (x = g.getOption(g.items[0])), !C.contains(x)) {
          let k = 0;
          d && !g.settings.addPrecedence && (k = 1), x = g.selectable()[k];
        }
      } else d && (x = d);
      t && !g.isOpen && (g.open(), g.scrollToOption(x, "auto")), g.setActiveOption(x);
    } else
      g.clearActiveOption(), t && g.isOpen && g.close(!1);
  }
  /**
   * Return list of selectable options
   *
   */
  selectable() {
    return this.dropdown_content.querySelectorAll("[data-selectable]");
  }
  /**
   * Adds an available option. If it already exists,
   * nothing will happen. Note: this does not refresh
   * the options list dropdown (use `refreshOptions`
   * for that).
   *
   * Usage:
   *
   *   this.addOption(data)
   *
   */
  addOption(t, e = !1) {
    const n = this;
    if (Array.isArray(t))
      return n.addOptions(t, e), !1;
    const r = Ct(t[n.settings.valueField]);
    return r === null || n.options.hasOwnProperty(r) ? !1 : (t.$order = t.$order || ++n.order, t.$id = n.inputId + "-opt-" + t.$order, n.options[r] = t, n.lastQuery = null, e && (n.userOptions[r] = e, n.trigger("option_add", r, t)), r);
  }
  /**
   * Add multiple options
   *
   */
  addOptions(t, e = !1) {
    rt(t, (n) => {
      this.addOption(n, e);
    });
  }
  /**
   * @deprecated 1.7.7
   */
  registerOption(t) {
    return this.addOption(t);
  }
  /**
   * Registers an option group to the pool of option groups.
   *
   * @return {boolean|string}
   */
  registerOptionGroup(t) {
    var e = Ct(t[this.settings.optgroupValueField]);
    return e === null ? !1 : (t.$order = t.$order || ++this.order, this.optgroups[e] = t, e);
  }
  /**
   * Registers a new optgroup for options
   * to be bucketed into.
   *
   */
  addOptionGroup(t, e) {
    var n;
    e[this.settings.optgroupValueField] = t, (n = this.registerOptionGroup(e)) && this.trigger("optgroup_add", n, e);
  }
  /**
   * Removes an existing option group.
   *
   */
  removeOptionGroup(t) {
    this.optgroups.hasOwnProperty(t) && (delete this.optgroups[t], this.clearCache(), this.trigger("optgroup_remove", t));
  }
  /**
   * Clears all existing option groups.
   */
  clearOptionGroups() {
    this.optgroups = {}, this.clearCache(), this.trigger("optgroup_clear");
  }
  /**
   * Updates an option available for selection. If
   * it is visible in the selected items or options
   * dropdown, it will be re-rendered automatically.
   *
   */
  updateOption(t, e) {
    const n = this;
    var r, s;
    const o = Ct(t), a = Ct(e[n.settings.valueField]);
    if (o === null)
      return;
    const c = n.options[o];
    if (c == null)
      return;
    if (typeof a != "string")
      throw new Error("Value must be set in option data");
    const l = n.getOption(o), h = n.getItem(o);
    if (e.$order = e.$order || c.$order, delete n.options[o], n.uncacheValue(a), n.options[a] = e, l) {
      if (n.dropdown_content.contains(l)) {
        const d = n._render("option", e);
        xn(l, d), n.activeOption === l && n.setActiveOption(d);
      }
      l.remove();
    }
    h && (s = n.items.indexOf(o), s !== -1 && n.items.splice(s, 1, a), r = n._render("item", e), h.classList.contains("active") && yt(r, "active"), xn(h, r)), n.lastQuery = null;
  }
  /**
   * Removes a single option.
   *
   */
  removeOption(t, e) {
    const n = this;
    t = ii(t), n.uncacheValue(t), delete n.userOptions[t], delete n.options[t], n.lastQuery = null, n.trigger("option_remove", t), n.removeItem(t, e);
  }
  /**
   * Clears all options.
   */
  clearOptions(t) {
    const e = (t || this.clearFilter).bind(this);
    this.loadedSearches = {}, this.userOptions = {}, this.clearCache();
    const n = {};
    rt(this.options, (r, s) => {
      e(r, s) && (n[s] = r);
    }), this.options = this.sifter.items = n, this.lastQuery = null, this.trigger("option_clear");
  }
  /**
   * Used by clearOptions() to decide whether or not an option should be removed
   * Return true to keep an option, false to remove
   *
   */
  clearFilter(t, e) {
    return this.items.indexOf(e) >= 0;
  }
  /**
   * Returns the dom element of the option
   * matching the given value.
   *
   */
  getOption(t, e = !1) {
    const n = Ct(t);
    if (n === null)
      return null;
    const r = this.options[n];
    if (r != null) {
      if (r.$div)
        return r.$div;
      if (e)
        return this._render("option", r);
    }
    return null;
  }
  /**
   * Returns the dom element of the next or previous dom element of the same type
   * Note: adjacent options may not be adjacent DOM elements (optgroups)
   *
   */
  getAdjacent(t, e, n = "option") {
    var r = this, s;
    if (!t)
      return null;
    n == "item" ? s = r.controlChildren() : s = r.dropdown_content.querySelectorAll("[data-selectable]");
    for (let o = 0; o < s.length; o++)
      if (s[o] == t)
        return e > 0 ? s[o + 1] : s[o - 1];
    return null;
  }
  /**
   * Returns the dom element of the item
   * matching the given value.
   *
   */
  getItem(t) {
    if (typeof t == "object")
      return t;
    var e = Ct(t);
    return e !== null ? this.control.querySelector(`[data-value="${Fr(e)}"]`) : null;
  }
  /**
   * "Selects" multiple items at once. Adds them to the list
   * at the current caret position.
   *
   */
  addItems(t, e) {
    var n = this, r = Array.isArray(t) ? t : [t];
    r = r.filter((o) => n.items.indexOf(o) === -1);
    const s = r[r.length - 1];
    r.forEach((o) => {
      n.isPending = o !== s, n.addItem(o, e);
    });
  }
  /**
   * "Selects" an item. Adds it to the list
   * at the current caret position.
   *
   */
  addItem(t, e) {
    var n = e ? [] : ["change", "dropdown_close"];
    Dr(this, n, () => {
      var r, s;
      const o = this, a = o.settings.mode, c = Ct(t);
      if (!(c && o.items.indexOf(c) !== -1 && (a === "single" && o.close(), a === "single" || !o.settings.duplicates)) && !(c === null || !o.options.hasOwnProperty(c)) && (a === "single" && o.clear(e), !(a === "multi" && o.isFull()))) {
        if (r = o._render("item", o.options[c]), o.control.contains(r) && (r = r.cloneNode(!0)), s = o.isFull(), o.items.splice(o.caretPos, 0, c), o.insertAtCaret(r), o.isSetup) {
          if (!o.isPending && o.settings.hideSelected) {
            let l = o.getOption(c), h = o.getAdjacent(l, 1);
            h && o.setActiveOption(h);
          }
          !o.isPending && !o.settings.closeAfterSelect && o.refreshOptions(o.isFocused && a !== "single"), o.settings.closeAfterSelect != !1 && o.isFull() ? o.close() : o.isPending || o.positionDropdown(), o.trigger("item_add", c, r), o.isPending || o.updateOriginalInput({ silent: e });
        }
        (!o.isPending || !s && o.isFull()) && (o.inputState(), o.refreshState());
      }
    });
  }
  /**
   * Removes the selected item matching
   * the provided value.
   *
   */
  removeItem(t = null, e) {
    const n = this;
    if (t = n.getItem(t), !t)
      return;
    var r, s;
    const o = t.dataset.value;
    r = Br(t), t.remove(), t.classList.contains("active") && (s = n.activeItems.indexOf(t), n.activeItems.splice(s, 1), Bt(t, "active")), n.items.splice(r, 1), n.lastQuery = null, !n.settings.persist && n.userOptions.hasOwnProperty(o) && n.removeOption(o, e), r < n.caretPos && n.setCaret(n.caretPos - 1), n.updateOriginalInput({ silent: e }), n.refreshState(), n.positionDropdown(), n.trigger("item_remove", o, t);
  }
  /**
   * Invokes the `create` method provided in the
   * TomSelect options that should provide the data
   * for the new item, given the user input.
   *
   * Once this completes, it will be added
   * to the item list.
   *
   */
  createItem(t = null, e = () => {
  }) {
    arguments.length === 3 && (e = arguments[2]), typeof e != "function" && (e = () => {
    });
    var n = this, r = n.caretPos, s;
    if (t = t || n.inputValue(), !n.canCreate(t))
      return e(), !1;
    n.lock();
    var o = !1, a = (c) => {
      if (n.unlock(), !c || typeof c != "object")
        return e();
      var l = Ct(c[n.settings.valueField]);
      if (typeof l != "string")
        return e();
      n.setTextboxValue(), n.addOption(c, !0), n.setCaret(r), n.addItem(l), e(c), o = !0;
    };
    return typeof n.settings.create == "function" ? s = n.settings.create.call(this, t, a) : s = {
      [n.settings.labelField]: t,
      [n.settings.valueField]: t
    }, o || a(s), !0;
  }
  /**
   * Re-renders the selected item lists.
   */
  refreshItems() {
    var t = this;
    t.lastQuery = null, t.isSetup && t.addItems(t.items), t.updateOriginalInput(), t.refreshState();
  }
  /**
   * Updates all state-dependent attributes
   * and CSS classes.
   */
  refreshState() {
    const t = this;
    t.refreshValidityState();
    const e = t.isFull(), n = t.isLocked;
    t.wrapper.classList.toggle("rtl", t.rtl);
    const r = t.wrapper.classList;
    r.toggle("focus", t.isFocused), r.toggle("disabled", t.isDisabled), r.toggle("readonly", t.isReadOnly), r.toggle("required", t.isRequired), r.toggle("invalid", !t.isValid), r.toggle("locked", n), r.toggle("full", e), r.toggle("input-active", t.isFocused && !t.isInputHidden), r.toggle("dropdown-active", t.isOpen), r.toggle("has-options", Wp(t.options)), r.toggle("has-items", t.items.length > 0);
  }
  /**
   * Update the `required` attribute of both input and control input.
   *
   * The `required` property needs to be activated on the control input
   * for the error to be displayed at the right place. `required` also
   * needs to be temporarily deactivated on the input since the input is
   * hidden and can't show errors.
   */
  refreshValidityState() {
    var t = this;
    t.input.validity && (t.isValid = t.input.validity.valid, t.isInvalid = !t.isValid);
  }
  /**
   * Determines whether or not more items can be added
   * to the control without exceeding the user-defined maximum.
   *
   * @returns {boolean}
   */
  isFull() {
    return this.settings.maxItems !== null && this.items.length >= this.settings.maxItems;
  }
  /**
   * Refreshes the original <select> or <input>
   * element to reflect the current state.
   *
   */
  updateOriginalInput(t = {}) {
    const e = this;
    var n, r;
    const s = e.input.querySelector('option[value=""]');
    if (e.is_select_tag) {
      let c = function(l, h, d) {
        return l || (l = Nt('<option value="' + Qi(h) + '">' + Qi(d) + "</option>")), l != s && e.input.append(l), o.push(l), (l != s || a > 0) && (l.selected = !0), l;
      };
      const o = [], a = e.input.querySelectorAll("option:checked").length;
      e.input.querySelectorAll("option:checked").forEach((l) => {
        l.selected = !1;
      }), e.items.length == 0 && e.settings.mode == "single" ? c(s, "", "") : e.items.forEach((l) => {
        if (n = e.options[l], r = n[e.settings.labelField] || "", o.includes(n.$option)) {
          const h = e.input.querySelector(`option[value="${Fr(l)}"]:not(:checked)`);
          c(h, l, r);
        } else
          n.$option = c(n.$option, l, r);
      });
    } else
      e.input.value = e.getValue();
    e.isSetup && (t.silent || e.trigger("change", e.getValue()));
  }
  /**
   * Shows the autocomplete dropdown containing
   * the available options.
   */
  open() {
    var t = this;
    t.isLocked || t.isOpen || t.settings.mode === "multi" && t.isFull() || (t.isOpen = !0, K(t.focus_node, { "aria-expanded": "true" }), t.refreshState(), Ue(t.dropdown, { visibility: "hidden", display: "block" }), t.positionDropdown(), Ue(t.dropdown, { visibility: "visible", display: "block" }), t.focus(), t.trigger("dropdown_open", t.dropdown));
  }
  /**
   * Closes the autocomplete dropdown menu.
   */
  close(t = !0) {
    var e = this, n = e.isOpen;
    t && (e.setTextboxValue(), e.settings.mode === "single" && e.items.length && e.inputState()), e.isOpen = !1, K(e.focus_node, { "aria-expanded": "false" }), Ue(e.dropdown, { display: "none" }), e.settings.hideSelected && e.clearActiveOption(), e.refreshState(), n && e.trigger("dropdown_close", e.dropdown);
  }
  /**
   * Calculates and applies the appropriate
   * position of the dropdown if dropdownParent = 'body'.
   * Otherwise, position is determined by css
   */
  positionDropdown() {
    if (this.settings.dropdownParent === "body") {
      var t = this.control, e = t.getBoundingClientRect(), n = t.offsetHeight + e.top + window.scrollY, r = e.left + window.scrollX;
      Ue(this.dropdown, {
        width: e.width + "px",
        top: n + "px",
        left: r + "px"
      });
    }
  }
  /**
   * Resets / clears all selected items
   * from the control.
   *
   */
  clear(t) {
    var e = this;
    if (e.items.length) {
      var n = e.controlChildren();
      rt(n, (r) => {
        e.removeItem(r, !0);
      }), e.inputState(), t || e.updateOriginalInput(), e.trigger("clear");
    }
  }
  /**
   * A helper method for inserting an element
   * at the current caret position.
   *
   */
  insertAtCaret(t) {
    const e = this, n = e.caretPos, r = e.control;
    r.insertBefore(t, r.children[n] || null), e.setCaret(n + 1);
  }
  /**
   * Removes the current selected item(s).
   *
   */
  deleteSelection(t) {
    var e, n, r, s, o = this;
    e = t && t.keyCode === Rr ? -1 : 1, n = Yp(o.control_input);
    const a = [];
    if (o.activeItems.length)
      s = zr(o.activeItems, e), r = Br(s), e > 0 && r++, rt(o.activeItems, (c) => a.push(c));
    else if ((o.isFocused || o.settings.mode === "single") && o.items.length) {
      const c = o.controlChildren();
      let l;
      e < 0 && n.start === 0 && n.length === 0 ? l = c[o.caretPos - 1] : e > 0 && n.start === o.inputValue().length && (l = c[o.caretPos]), l !== void 0 && a.push(l);
    }
    if (!o.shouldDelete(a, t))
      return !1;
    for (J(t, !0), typeof r < "u" && o.setCaret(r); a.length; )
      o.removeItem(a.pop());
    return o.inputState(), o.positionDropdown(), o.refreshOptions(!1), !0;
  }
  /**
   * Return true if the items should be deleted
   */
  shouldDelete(t, e) {
    const n = t.map((r) => r.dataset.value);
    return !(!n.length || typeof this.settings.onDelete == "function" && this.settings.onDelete(n, e) === !1);
  }
  /**
   * Selects the previous / next item (depending on the `direction` argument).
   *
   * > 0 - right
   * < 0 - left
   *
   */
  advanceSelection(t, e) {
    var n, r, s = this;
    s.rtl && (t *= -1), !s.inputValue().length && (Ut(je, e) || Ut("shiftKey", e) ? (n = s.getLastActive(t), n ? n.classList.contains("active") ? r = s.getAdjacent(n, t, "item") : r = n : t > 0 ? r = s.control_input.nextElementSibling : r = s.control_input.previousElementSibling, r && (r.classList.contains("active") && s.removeActiveItem(n), s.setActiveItemClass(r))) : s.moveCaret(t));
  }
  moveCaret(t) {
  }
  /**
   * Get the last active item
   *
   */
  getLastActive(t) {
    let e = this.control.querySelector(".last-active");
    if (e)
      return e;
    var n = this.control.querySelectorAll(".active");
    if (n)
      return zr(n, t);
  }
  /**
   * Moves the caret to the specified index.
   *
   * The input must be moved by leaving it in place and moving the
   * siblings, due to the fact that focus cannot be restored once lost
   * on mobile webkit devices
   *
   */
  setCaret(t) {
    this.caretPos = this.items.length;
  }
  /**
   * Return list of item dom elements
   *
   */
  controlChildren() {
    return Array.from(this.control.querySelectorAll("[data-ts-item]"));
  }
  /**
   * Disables user input on the control. Used while
   * items are being asynchronously created.
   */
  lock() {
    this.setLocked(!0);
  }
  /**
   * Re-enables user input on the control.
   */
  unlock() {
    this.setLocked(!1);
  }
  /**
   * Disable or enable user input on the control
   */
  setLocked(t = this.isReadOnly || this.isDisabled) {
    this.isLocked = t, this.refreshState();
  }
  /**
   * Disables user input on the control completely.
   * While disabled, it cannot receive focus.
   */
  disable() {
    this.setDisabled(!0), this.close();
  }
  /**
   * Enables the control so that it can respond
   * to focus and user input.
   */
  enable() {
    this.setDisabled(!1);
  }
  setDisabled(t) {
    this.focus_node.tabIndex = t ? -1 : this.tabIndex, this.isDisabled = t, this.input.disabled = t, this.control_input.disabled = t, this.setLocked();
  }
  setReadOnly(t) {
    this.isReadOnly = t, this.input.readOnly = t, this.control_input.readOnly = t, this.setLocked();
  }
  /**
   * Completely destroys the control and
   * unbinds all event listeners so that it can
   * be garbage collected.
   */
  destroy() {
    var t = this, e = t.revertSettings;
    t.trigger("destroy"), t.off(), t.wrapper.remove(), t.dropdown.remove(), t.input.innerHTML = e.innerHTML, t.input.tabIndex = e.tabIndex, Bt(t.input, "tomselected", "ts-hidden-accessible"), t._destroy(), delete t.input.tomselect;
  }
  /**
   * A helper method for rendering "item" and
   * "option" templates, given the data.
   *
   */
  render(t, e) {
    var n, r;
    const s = this;
    if (typeof this.settings.render[t] != "function" || (r = s.settings.render[t].call(this, e, Qi), !r))
      return null;
    if (r = Nt(r), t === "option" || t === "option_create" ? e[s.settings.disabledField] ? K(r, { "aria-disabled": "true" }) : K(r, { "data-selectable": "" }) : t === "optgroup" && (n = e.group[s.settings.optgroupValueField], K(r, { "data-group": n }), e.group[s.settings.disabledField] && K(r, { "data-disabled": "" })), t === "option" || t === "item") {
      const o = ii(e[s.settings.valueField]);
      K(r, { "data-value": o }), t === "item" ? (yt(r, s.settings.itemClass), K(r, { "data-ts-item": "" })) : (yt(r, s.settings.optionClass), K(r, {
        role: "option",
        id: e.$id
      }), e.$div = r, s.options[o] = e);
    }
    return r;
  }
  /**
   * Type guarded rendering
   *
   */
  _render(t, e) {
    const n = this.render(t, e);
    if (n == null)
      throw "HTMLElement expected";
    return n;
  }
  /**
   * Clears the render cache for a template. If
   * no template is given, clears all render
   * caches.
   *
   */
  clearCache() {
    rt(this.options, (t) => {
      t.$div && (t.$div.remove(), delete t.$div);
    });
  }
  /**
   * Removes a value from item and option caches
   *
   */
  uncacheValue(t) {
    const e = this.getOption(t);
    e && e.remove();
  }
  /**
   * Determines whether or not to display the
   * create item prompt, given a user input.
   *
   */
  canCreate(t) {
    return this.settings.create && t.length > 0 && this.settings.createFilter.call(this, t);
  }
  /**
   * Wraps this.`method` so that `new_fn` can be invoked 'before', 'after', or 'instead' of the original method
   *
   * this.hook('instead','onKeyDown',function( arg1, arg2 ...){
   *
   * });
   */
  hook(t, e, n) {
    var r = this, s = r[e];
    r[e] = function() {
      var o, a;
      return t === "after" && (o = s.apply(r, arguments)), a = n.apply(r, arguments), t === "instead" ? a : (t === "before" && (o = s.apply(r, arguments)), o);
    };
  }
}
const lf = (i, t, e, n) => {
  i.addEventListener(t, e, n);
};
function cf() {
  lf(this.input, "change", () => {
    this.sync();
  });
}
const hf = (i) => typeof i > "u" || i === null ? null : df(i), df = (i) => typeof i == "boolean" ? i ? "1" : "0" : i + "", Vr = (i, t = !1) => {
  i && (i.preventDefault(), t && i.stopPropagation());
}, uf = (i) => {
  if (i.jquery)
    return i[0];
  if (i instanceof HTMLElement)
    return i;
  if (pf(i)) {
    var t = document.createElement("template");
    return t.innerHTML = i.trim(), t.content.firstChild;
  }
  return document.querySelector(i);
}, pf = (i) => typeof i == "string" && i.indexOf("<") > -1;
function ff(i) {
  var t = this, e = t.onOptionSelect;
  t.settings.hideSelected = !1;
  const n = Object.assign({
    // so that the user may add different ones as well
    className: "tomselect-checkbox",
    // the following default to the historic plugin's values
    checkedClassNames: void 0,
    uncheckedClassNames: void 0
  }, i);
  var r = function(a, c) {
    c ? (a.checked = !0, n.uncheckedClassNames && a.classList.remove(...n.uncheckedClassNames), n.checkedClassNames && a.classList.add(...n.checkedClassNames)) : (a.checked = !1, n.checkedClassNames && a.classList.remove(...n.checkedClassNames), n.uncheckedClassNames && a.classList.add(...n.uncheckedClassNames));
  }, s = function(a) {
    setTimeout(() => {
      var c = a.querySelector("input." + n.className);
      c instanceof HTMLInputElement && r(c, a.classList.contains("selected"));
    }, 1);
  };
  t.hook("after", "setupTemplates", () => {
    var o = t.settings.render.option;
    t.settings.render.option = (a, c) => {
      var l = uf(o.call(t, a, c)), h = document.createElement("input");
      n.className && h.classList.add(n.className), h.addEventListener("click", function(u) {
        Vr(u);
      }), h.type = "checkbox";
      const d = hf(a[t.settings.valueField]);
      return r(h, !!(d && t.items.indexOf(d) > -1)), l.prepend(h), l;
    };
  }), t.on("item_remove", (o) => {
    var a = t.getOption(o);
    a && (a.classList.remove("selected"), s(a));
  }), t.on("item_add", (o) => {
    var a = t.getOption(o);
    a && s(a);
  }), t.hook("instead", "onOptionSelect", (o, a) => {
    if (a.classList.contains("selected")) {
      a.classList.remove("selected"), t.removeItem(a.dataset.value), t.refreshOptions(), Vr(o, !0);
      return;
    }
    e.call(t, o, a), s(a);
  });
}
const gf = (i) => {
  if (i.jquery)
    return i[0];
  if (i instanceof HTMLElement)
    return i;
  if (mf(i)) {
    var t = document.createElement("template");
    return t.innerHTML = i.trim(), t.content.firstChild;
  }
  return document.querySelector(i);
}, mf = (i) => typeof i == "string" && i.indexOf("<") > -1;
function vf(i) {
  const t = this, e = Object.assign({
    className: "clear-button",
    title: "Clear All",
    html: (n) => `<div class="${n.className}" title="${n.title}">&#10799;</div>`
  }, i);
  t.on("initialize", () => {
    var n = gf(e.html(e));
    n.addEventListener("click", (r) => {
      t.isLocked || (t.clear(), t.settings.mode === "single" && t.settings.allowEmptyOption && t.addItem(""), r.preventDefault(), r.stopPropagation());
    }), t.control.appendChild(n);
  });
}
const yf = (i, t = !1) => {
  i && (i.preventDefault(), t && i.stopPropagation());
}, te = (i, t, e, n) => {
  i.addEventListener(t, e, n);
}, bf = (i, t) => {
  if (Array.isArray(i))
    i.forEach(t);
  else
    for (var e in i)
      i.hasOwnProperty(e) && t(i[e], e);
}, wf = (i) => {
  if (i.jquery)
    return i[0];
  if (i instanceof HTMLElement)
    return i;
  if (xf(i)) {
    var t = document.createElement("template");
    return t.innerHTML = i.trim(), t.content.firstChild;
  }
  return document.querySelector(i);
}, xf = (i) => typeof i == "string" && i.indexOf("<") > -1, Cf = (i, t) => {
  bf(t, (e, n) => {
    e == null ? i.removeAttribute(n) : i.setAttribute(n, "" + e);
  });
}, Mf = (i, t) => {
  var e;
  (e = i.parentNode) == null || e.insertBefore(t, i.nextSibling);
}, Ef = (i, t) => {
  var e;
  (e = i.parentNode) == null || e.insertBefore(t, i);
}, Sf = (i, t) => {
  do {
    var e;
    if (t = (e = t) == null ? void 0 : e.previousElementSibling, i == t)
      return !0;
  } while (t && t.previousElementSibling);
  return !1;
};
function _f() {
  var i = this;
  if (i.settings.mode !== "multi") return;
  var t = i.lock, e = i.unlock;
  let n = !0, r;
  i.hook("after", "setupTemplates", () => {
    var s = i.settings.render.item;
    i.settings.render.item = (o, a) => {
      const c = wf(s.call(i, o, a));
      Cf(c, {
        draggable: "true"
      });
      const l = (v) => {
        n || yf(v), v.stopPropagation();
      }, h = (v) => {
        r = c, setTimeout(() => {
          c.classList.add("ts-dragging");
        }, 0);
      }, d = (v) => {
        v.preventDefault(), c.classList.add("ts-drag-over"), p(c, r);
      }, u = () => {
        c.classList.remove("ts-drag-over");
      }, p = (v, y) => {
        y !== void 0 && (Sf(y, c) ? Mf(v, y) : Ef(v, y));
      }, g = () => {
        var v;
        document.querySelectorAll(".ts-drag-over").forEach((b) => b.classList.remove("ts-drag-over")), (v = r) == null || v.classList.remove("ts-dragging"), r = void 0;
        var y = [];
        i.control.querySelectorAll("[data-value]").forEach((b) => {
          if (b.dataset.value) {
            let x = b.dataset.value;
            x && y.push(x);
          }
        }), i.setValue(y);
      };
      return te(c, "mousedown", l), te(c, "dragstart", h), te(c, "dragenter", d), te(c, "dragover", d), te(c, "dragleave", u), te(c, "dragend", g), c;
    };
  }), i.hook("instead", "lock", () => (n = !1, t.call(i))), i.hook("instead", "unlock", () => (n = !0, e.call(i)));
}
const kf = (i, t = !1) => {
  i && (i.preventDefault(), t && i.stopPropagation());
}, Nf = (i) => {
  if (i.jquery)
    return i[0];
  if (i instanceof HTMLElement)
    return i;
  if (Af(i)) {
    var t = document.createElement("template");
    return t.innerHTML = i.trim(), t.content.firstChild;
  }
  return document.querySelector(i);
}, Af = (i) => typeof i == "string" && i.indexOf("<") > -1;
function If(i) {
  const t = this, e = Object.assign({
    title: "Untitled",
    headerClass: "dropdown-header",
    titleRowClass: "dropdown-header-title",
    labelClass: "dropdown-header-label",
    closeClass: "dropdown-header-close",
    html: (n) => '<div class="' + n.headerClass + '"><div class="' + n.titleRowClass + '"><span class="' + n.labelClass + '">' + n.title + '</span><a class="' + n.closeClass + '">&times;</a></div></div>'
  }, i);
  t.on("initialize", () => {
    var n = Nf(e.html(e)), r = n.querySelector("." + e.closeClass);
    r && r.addEventListener("click", (s) => {
      kf(s, !0), t.close();
    }), t.dropdown.insertBefore(n, t.dropdown.firstChild);
  });
}
const Lf = (i, t) => {
  if (Array.isArray(i))
    i.forEach(t);
  else
    for (var e in i)
      i.hasOwnProperty(e) && t(i[e], e);
}, Of = (i, ...t) => {
  var e = Tf(t);
  i = Pf(i), i.map((n) => {
    e.map((r) => {
      n.classList.remove(r);
    });
  });
}, Tf = (i) => {
  var t = [];
  return Lf(i, (e) => {
    typeof e == "string" && (e = e.trim().split(/[\t\n\f\r\s]/)), Array.isArray(e) && (t = t.concat(e));
  }), t.filter(Boolean);
}, Pf = (i) => (Array.isArray(i) || (i = [i]), i), Df = (i, t) => {
  if (!i) return -1;
  t = t || i.nodeName;
  for (var e = 0; i = i.previousElementSibling; )
    i.matches(t) && e++;
  return e;
};
function Ff() {
  var i = this;
  i.hook("instead", "setCaret", (t) => {
    i.settings.mode === "single" || !i.control.contains(i.control_input) ? t = i.items.length : (t = Math.max(0, Math.min(i.items.length, t)), t != i.caretPos && !i.isPending && i.controlChildren().forEach((e, n) => {
      n < t ? i.control_input.insertAdjacentElement("beforebegin", e) : i.control.appendChild(e);
    })), i.caretPos = t;
  }), i.hook("instead", "moveCaret", (t) => {
    if (!i.isFocused) return;
    const e = i.getLastActive(t);
    if (e) {
      const n = Df(e);
      i.setCaret(t > 0 ? n + 1 : n), i.setActiveItem(), Of(e, "last-active");
    } else
      i.setCaret(i.caretPos + t);
  });
}
const zf = 27, Bf = 9, Rf = (i, t = !1) => {
  i && (i.preventDefault(), t && i.stopPropagation());
}, Hf = (i, t, e, n) => {
  i.addEventListener(t, e, n);
}, $f = (i, t) => {
  if (Array.isArray(i))
    i.forEach(t);
  else
    for (var e in i)
      i.hasOwnProperty(e) && t(i[e], e);
}, Ur = (i) => {
  if (i.jquery)
    return i[0];
  if (i instanceof HTMLElement)
    return i;
  if (Gf(i)) {
    var t = document.createElement("template");
    return t.innerHTML = i.trim(), t.content.firstChild;
  }
  return document.querySelector(i);
}, Gf = (i) => typeof i == "string" && i.indexOf("<") > -1, qf = (i, ...t) => {
  var e = Vf(t);
  i = Uf(i), i.map((n) => {
    e.map((r) => {
      n.classList.add(r);
    });
  });
}, Vf = (i) => {
  var t = [];
  return $f(i, (e) => {
    typeof e == "string" && (e = e.trim().split(/[\t\n\f\r\s]/)), Array.isArray(e) && (t = t.concat(e));
  }), t.filter(Boolean);
}, Uf = (i) => (Array.isArray(i) || (i = [i]), i);
function jf() {
  const i = this;
  i.settings.shouldOpen = !0, i.hook("before", "setup", () => {
    i.focus_node = i.control, qf(i.control_input, "dropdown-input");
    const t = Ur('<div class="dropdown-input-wrap">');
    t.append(i.control_input), i.dropdown.insertBefore(t, i.dropdown.firstChild);
    const e = Ur('<input class="items-placeholder" tabindex="-1" />');
    e.placeholder = i.settings.placeholder || "", i.control.append(e);
  }), i.on("initialize", () => {
    i.control_input.addEventListener("keydown", (e) => {
      switch (e.keyCode) {
        case zf:
          i.isOpen && (Rf(e, !0), i.close()), i.clearActiveItems();
          return;
        case Bf:
          i.focus_node.tabIndex = -1;
          break;
      }
      return i.onKeyDown.call(i, e);
    }), i.on("blur", () => {
      i.focus_node.tabIndex = i.isDisabled ? -1 : i.tabIndex;
    }), i.on("dropdown_open", () => {
      i.control_input.focus();
    });
    const t = i.onBlur;
    i.hook("instead", "onBlur", (e) => {
      if (!(e && e.relatedTarget == i.control_input))
        return t.call(i);
    }), Hf(i.control_input, "blur", () => i.onBlur()), i.hook("before", "close", () => {
      i.isOpen && i.focus_node.focus({
        preventScroll: !0
      });
    });
  });
}
const Ye = (i, t, e, n) => {
  i.addEventListener(t, e, n);
};
function Yf() {
  var i = this;
  i.on("initialize", () => {
    var t = document.createElement("span"), e = i.control_input;
    t.style.cssText = "position:absolute; top:-99999px; left:-99999px; width:auto; padding:0; white-space:pre; ", i.wrapper.appendChild(t);
    var n = ["letterSpacing", "fontSize", "fontFamily", "fontWeight", "textTransform"];
    for (const s of n)
      t.style[s] = e.style[s];
    var r = () => {
      t.textContent = e.value, e.style.width = t.clientWidth + "px";
    };
    r(), i.on("update item_add item_remove", r), Ye(e, "input", r), Ye(e, "keyup", r), Ye(e, "blur", r), Ye(e, "update", r);
  });
}
function Xf() {
  var i = this, t = i.deleteSelection;
  this.hook("instead", "deleteSelection", (e) => i.activeItems.length ? t.call(i, e) : !1);
}
function Wf() {
  this.hook("instead", "setActiveItem", () => {
  }), this.hook("instead", "selectAll", () => {
  });
}
const jr = 37, Kf = 39, Zf = (i, t, e) => {
  for (; i && i.matches; ) {
    if (i.matches(t))
      return i;
    i = i.parentNode;
  }
}, Qf = (i, t) => {
  if (!i) return -1;
  t = t || i.nodeName;
  for (var e = 0; i = i.previousElementSibling; )
    i.matches(t) && e++;
  return e;
};
function Jf() {
  var i = this, t = i.onKeyDown;
  i.hook("instead", "onKeyDown", (e) => {
    var n, r, s, o;
    if (!i.isOpen || !(e.keyCode === jr || e.keyCode === Kf))
      return t.call(i, e);
    i.ignoreHover = !0, o = Zf(i.activeOption, "[data-group]"), n = Qf(i.activeOption, "[data-selectable]"), o && (e.keyCode === jr ? o = o.previousSibling : o = o.nextSibling, o && (s = o.querySelectorAll("[data-selectable]"), r = s[Math.min(s.length - 1, n)], r && i.setActiveOption(r)));
  });
}
const tg = (i) => (i + "").replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;"), Yr = (i, t = !1) => {
  i && (i.preventDefault(), t && i.stopPropagation());
}, Xr = (i, t, e, n) => {
  i.addEventListener(t, e, n);
}, Wr = (i) => {
  if (i.jquery)
    return i[0];
  if (i instanceof HTMLElement)
    return i;
  if (eg(i)) {
    var t = document.createElement("template");
    return t.innerHTML = i.trim(), t.content.firstChild;
  }
  return document.querySelector(i);
}, eg = (i) => typeof i == "string" && i.indexOf("<") > -1;
function ig(i) {
  const t = Object.assign({
    label: "&times;",
    title: "Remove",
    className: "remove",
    append: !0
  }, i);
  var e = this;
  if (t.append) {
    var n = '<a href="javascript:void(0)" class="' + t.className + '" tabindex="-1" title="' + tg(t.title) + '">' + t.label + "</a>";
    e.hook("after", "setupTemplates", () => {
      var r = e.settings.render.item;
      e.settings.render.item = (s, o) => {
        var a = Wr(r.call(e, s, o)), c = Wr(n);
        return a.appendChild(c), Xr(c, "mousedown", (l) => {
          Yr(l, !0);
        }), Xr(c, "click", (l) => {
          e.isLocked || (Yr(l, !0), !e.isLocked && e.shouldDelete([a], l) && (e.removeItem(a), e.refreshOptions(!1), e.inputState()));
        }), a;
      };
    });
  }
}
function ng(i) {
  const t = this, e = Object.assign({
    text: (n) => n[t.settings.labelField]
  }, i);
  t.on("item_remove", function(n) {
    if (t.isFocused && t.control_input.value.trim() === "") {
      var r = t.options[n];
      r && t.setTextboxValue(e.text.call(t, r));
    }
  });
}
const rg = (i, t) => {
  if (Array.isArray(i))
    i.forEach(t);
  else
    for (var e in i)
      i.hasOwnProperty(e) && t(i[e], e);
}, sg = (i, ...t) => {
  var e = og(t);
  i = ag(i), i.map((n) => {
    e.map((r) => {
      n.classList.add(r);
    });
  });
}, og = (i) => {
  var t = [];
  return rg(i, (e) => {
    typeof e == "string" && (e = e.trim().split(/[\t\n\f\r\s]/)), Array.isArray(e) && (t = t.concat(e));
  }), t.filter(Boolean);
}, ag = (i) => (Array.isArray(i) || (i = [i]), i);
function lg() {
  const i = this, t = i.canLoad, e = i.clearActiveOption, n = i.loadCallback;
  var r = {}, s, o = !1, a, c = [];
  if (i.settings.shouldLoadMore || (i.settings.shouldLoadMore = () => {
    if (s.clientHeight / (s.scrollHeight - s.scrollTop) > 0.9)
      return !0;
    if (i.activeOption) {
      var u = i.selectable(), p = Array.from(u).indexOf(i.activeOption);
      if (p >= u.length - 2)
        return !0;
    }
    return !1;
  }), !i.settings.firstUrl)
    throw "virtual_scroll plugin requires a firstUrl() method";
  i.settings.sortField = [{
    field: "$order"
  }, {
    field: "$score"
  }];
  const l = (d) => typeof i.settings.maxOptions == "number" && s.children.length >= i.settings.maxOptions ? !1 : !!(d in r && r[d]), h = (d, u) => i.items.indexOf(u) >= 0 || c.indexOf(u) >= 0;
  i.setNextUrl = (d, u) => {
    r[d] = u;
  }, i.getUrl = (d) => {
    if (d in r) {
      const u = r[d];
      return r[d] = !1, u;
    }
    return i.clearPagination(), i.settings.firstUrl.call(i, d);
  }, i.clearPagination = () => {
    r = {};
  }, i.hook("instead", "clearActiveOption", () => {
    if (!o)
      return e.call(i);
  }), i.hook("instead", "canLoad", (d) => d in r ? l(d) : t.call(i, d)), i.hook("instead", "loadCallback", (d, u) => {
    if (!o)
      i.clearOptions(h);
    else if (a) {
      const p = d[0];
      p !== void 0 && (a.dataset.value = p[i.settings.valueField]);
    }
    n.call(i, d, u), o = !1;
  }), i.hook("after", "refreshOptions", () => {
    const d = i.lastValue;
    var u;
    l(d) ? (u = i.render("loading_more", {
      query: d
    }), u && (u.setAttribute("data-selectable", ""), a = u)) : d in r && !s.querySelector(".no-results") && (u = i.render("no_more_results", {
      query: d
    })), u && (sg(u, i.settings.optionClass), s.append(u));
  }), i.on("initialize", () => {
    c = Object.keys(i.options), s = i.dropdown_content, i.settings.render = Object.assign({}, {
      loading_more: () => '<div class="loading-more-results">Loading more results ... </div>',
      no_more_results: () => '<div class="no-more-results">No more results</div>'
    }, i.settings.render), s.addEventListener("scroll", () => {
      i.settings.shouldLoadMore.call(i) && l(i.lastValue) && (o || (o = !0, i.load.call(i, i.lastValue)));
    });
  });
}
at.define("change_listener", cf);
at.define("checkbox_options", ff);
at.define("clear_button", vf);
at.define("drag_drop", _f);
at.define("dropdown_header", If);
at.define("caret_position", Ff);
at.define("dropdown_input", jf);
at.define("input_autogrow", Yf);
at.define("no_backspace_delete", Xf);
at.define("no_active_items", Wf);
at.define("optgroup_columns", Jf);
at.define("remove_button", ig);
at.define("restore_on_backspace", ng);
at.define("virtual_scroll", lg);
class nn {
  static createForm(t) {
    const e = document.createElement("form");
    return e.className = "pvt-form", t.fields.forEach((n) => {
      e.appendChild(this.createField(n));
    }), e;
  }
  static getValues(t) {
    const e = {};
    return t.querySelectorAll("[data-field-key]").forEach((r) => {
      const s = r.getAttribute("data-field-key");
      switch (r.getAttribute("data-field-type")) {
        case "text":
          e[s] = r.value || void 0;
          break;
        case "select": {
          const a = r;
          e[s] = a.value || void 0, a.dataset.fieldValuesAreBoolean === "yes" && e[s] !== void 0 && e[s] === "true" && (e[s] = !0);
          break;
        }
        case "multiselect": {
          const a = r;
          e[s] = Array.from(
            a.selectedOptions
          ).map((c) => c.value), a.dataset.fieldValuesAreBoolean === "yes" && e[s].map((c) => c !== void 0 && c === "true" ? !0 : c);
          break;
        }
        case "checkbox":
          e[s] = r.checked;
          break;
        case "numberRange": {
          const a = r.querySelector(".min").value, c = r.querySelector(".max").value;
          e[s] = {
            min: a ? Number(a) : void 0,
            max: c ? Number(c) : void 0
          };
          break;
        }
      }
    }), e;
  }
  static clear(t) {
    t.reset(), t.querySelectorAll("select").forEach((e) => {
      var n;
      (n = e.tomselect) == null || n.sync();
    });
  }
  static createField(t) {
    const e = document.createElement("div");
    e.className = "pvt-form-element";
    const n = document.createElement("label");
    switch (n.htmlFor = `pvt-form-element-${t.key}`, n.textContent = this.niceLabelFromKey(t.label), e.appendChild(n), t.type) {
      case "select":
        e.appendChild(this.createSelect(t));
        break;
      case "multiselect":
        e.appendChild(this.createMultiSelect(t));
        break;
      case "checkbox":
        e.appendChild(this.createCheckbox(t));
        break;
      case "text":
        e.appendChild(this.createText(t));
        break;
      case "numberRange":
        e.appendChild(this.createNumberRange(t));
        break;
    }
    return e;
  }
  static baseAttrs(t, e) {
    t.id = `pvt-form-element-${e.key}`, t.setAttribute("data-field-key", e.key), t.setAttribute("data-field-type", e.type);
  }
  static buildSelect(t) {
    var n;
    const e = document.createElement("select");
    if (this.baseAttrs(e, t), t.allowEmpty) {
      const r = document.createElement("option");
      r.value = "", r.textContent = "", r.selected = !0, e.appendChild(r);
    }
    return t.valuesAreBoolean && e.setAttribute("data-field-values-are-boolean", "yes"), (n = t.options) == null || n.forEach((r) => {
      const s = document.createElement("option");
      s.value = r.value, s.textContent = r.label, t.defaultValue && (Array.isArray(t.defaultValue) ? t.defaultValue.includes(r.value) : t.defaultValue === r.value) && (s.selected = !0), e.appendChild(s);
    }), e;
  }
  static createSelect(t) {
    const e = this.buildSelect(t);
    return requestAnimationFrame(() => {
      const n = {
        plugins: {
          clear_button: {
            title: "Remove all selected options"
          }
        }
      };
      new at(e, n);
    }), e;
  }
  static createMultiSelect(t) {
    const e = this.buildSelect(t);
    return e.multiple = !0, requestAnimationFrame(() => {
      const n = {
        plugins: {
          checkbox_options: {
            checkedClassNames: ["pvt-ts-checked"],
            uncheckedClassNames: ["pvt-ts-unchecked"]
          },
          clear_button: {
            title: "Remove all selected options"
          },
          remove_button: {
            title: "Remove this item"
          }
        }
      };
      new at(e, n);
    }), e;
  }
  static createCheckbox(t) {
    const e = document.createElement("input");
    return e.type = "checkbox", t.defaultValue === !0 && (e.checked = !0), this.baseAttrs(e, t), e;
  }
  static createText(t) {
    const e = document.createElement("input");
    return e.type = "text", e.placeholder = t.placeholder ?? "", this.baseAttrs(e, t), t.defaultValue && (e.value = String(t.defaultValue)), e;
  }
  static createNumberRange(t) {
    const e = document.createElement("div");
    e.className = "pvt-number-range", this.baseAttrs(e, t);
    const n = document.createElement("input");
    n.type = "number", n.placeholder = "Min", n.className = "min";
    const r = document.createElement("input");
    r.type = "number", r.placeholder = "Max", r.className = "max";
    const s = typeof t.defaultValue == "object" && t.defaultValue !== null ? t.defaultValue : void 0;
    return (s == null ? void 0 : s.min) != null && (n.value = String(s.min)), (s == null ? void 0 : s.max) != null && (r.value = String(s.max)), e.append(n, r), e;
  }
  static niceLabelFromKey(t) {
    return t.replace(/([A-Z])/g, " $1").replace(/[_-]+/g, " ").trim().split(" ").map((n) => n.charAt(0).toUpperCase() + n.slice(1).toLowerCase()).join(" ");
  }
}
const cg = "Filter Graph";
class hg {
  constructor(t) {
    f(this, "uiManager");
    f(this, "graphFilter");
    f(this, "formOptions");
    f(this, "manuallyFilteredContainer");
    this.uiManager = t, this.formOptions = [];
  }
  mount(t) {
    t && (this.build(), this.graphFilter && t.appendChild(this.graphFilter));
  }
  destroy() {
    var t;
    (t = this.graphFilter) == null || t.remove(), this.graphFilter = void 0;
  }
  afterMount() {
  }
  graphReady() {
  }
  build() {
    return this.graphFilter = document.createElement("div"), this.graphFilter.classList.add("pvt-graph-filter-container"), this.uiManager.graph.on("dataBatchChanged", () => {
      this.rebuild();
    }), this.uiManager.graph.queryEngine.on("filterChange", (t) => {
      this.updateUIFilterButtonContent(t), this.updateUIFilterHiddenNodes();
    }), requestAnimationFrame(() => {
      this.updateUIFilterButtonContent({}), this.updateUIFilterHiddenNodes();
    }), this.graphFilter;
  }
  rebuild() {
    var a;
    if (!this.graphFilter) return;
    const t = ft({
      variant: "secondary",
      text: "Reset",
      size: "sm",
      style: "align-self: end;",
      svgIcon: ju,
      onClick: () => {
        nn.clear(n);
        const c = {};
        this.filterGraph(c);
      }
    }), e = this.getAvailableNodeAttributes();
    this.formOptions = Object.entries(e).map(([c, l]) => {
      let h = "text", d = "exact", u = !1;
      l.values ? l.values && l.values.every((g) => g.length < 64) ? l.values.length > 2 ? (h = "multiselect", d = "partial") : h = "select" : l.values.every((g) => typeof g == "boolean") && (h = "select", l.values = ["true", "false"], u = !0) : h = "numberRange";
      const p = {
        key: c,
        label: c,
        type: h,
        matchMode: d,
        valuesAreBoolean: u
      };
      return (p.type == "select" || p.type == "multiselect") && l.values && (p.options = l.values.map((g) => ({
        label: g,
        value: g
      })), p.allowEmpty = !0), p;
    });
    const n = nn.createForm({
      fields: this.formOptions
    }), r = ft({
      variant: "primary",
      text: "Filter Graph",
      size: "block",
      style: "margin-top: 16px;",
      svgIcon: zs,
      onClick: () => {
        const c = nn.getValues(n);
        this.filterGraph(c);
      }
    }), s = T("div", { class: "pvt-sidebar-separator" });
    this.manuallyFilteredContainer = ot(`<div class="pvt-hidden-nodes-container">
                <h4>Hidden nodes</h4>
                <div class="pvt-hidden-nodes-container-list"></div>
            </div>`);
    const o = ft({
      variant: "secondary",
      text: "Show all nodes",
      size: "sm",
      style: "align-self: end;",
      svgIcon: Ir,
      onClick: () => {
        this.uiManager.graph.queryEngine.clearNodeExclusions();
      },
      title: "Restore manually hidden nodes"
    });
    (a = this.manuallyFilteredContainer.querySelector("h4")) == null || a.appendChild(o), this.graphFilter.appendChild(t), this.graphFilter.appendChild(n), this.graphFilter.appendChild(r), this.graphFilter.appendChild(s), this.graphFilter.appendChild(this.manuallyFilteredContainer);
  }
  updateUIFilterButtonContent(t) {
    var o, a;
    const e = (o = this.uiManager.toolbar) == null ? void 0 : o.filterButton, n = e == null ? void 0 : e.querySelector(".action-text");
    if (!n) return;
    n.innerHTML = "";
    let r = Object.keys(t).length;
    const s = (a = t.manuallyHidden) == null ? void 0 : a.value;
    if (Array.isArray(s) && s.length == 0 && r--, r > 0) {
      const c = r > 1 ? `${r} active filters` : "1 active filter", l = this.uiManager.graph.queryEngine.getHiddenNodeCount(), h = T(
        "span",
        {
          class: "active-filter-subtext"
        },
        [
          T("span", {}, ["·"]),
          T("span", {}, [`${l} hidden`])
        ]
      ), d = Gs({
        text: c,
        html: h,
        variant: "primary",
        size: "sm"
      });
      n.appendChild(d);
    } else
      n.textContent = cg;
  }
  updateUIFilterHiddenNodes() {
    if (!this.manuallyFilteredContainer) return;
    const t = this.manuallyFilteredContainer.querySelector(".pvt-hidden-nodes-container-list");
    t && (this.uiManager.graph.queryEngine.getExcludedNodeCount() > 0 ? (this.manuallyFilteredContainer.classList.remove("hidden"), t.innerHTML = "", this.uiManager.graph.queryEngine.getExcludedNodes().forEach((e) => {
      const n = Object.keys(e.getData()).length, r = e.getEdgesIn().length + e.getEdgesOut().length, s = ft({
        variant: "secondary",
        text: "Show node",
        size: "sm",
        title: "Restore manually hidden node",
        svgIcon: Ir,
        onClick: () => {
          this.uiManager.graph.queryEngine.includeNode(e);
        }
      }), o = T(
        "span",
        {
          class: "subtext"
        },
        [
          T("span", { class: "nodeinfo" }, [n.toString(), Y({ svgIcon: np })]),
          "·",
          T("span", { class: "nodeinfo" }, [r.toString(), Y({ svgIcon: pi(24) })])
        ]
      ), a = T(
        "div",
        {
          class: "hidden-node"
        },
        [
          Wt(e, this.uiManager.getOptions().mainHeader),
          o,
          s
        ]
      );
      a.addEventListener("mouseenter", (c) => {
        var l;
        (l = this.uiManager.tooltip) == null || l.openForNodeOnElement(c, e);
      }), a.addEventListener("mouseleave", () => {
        var c;
        (c = this.uiManager.tooltip) == null || c.hide();
      }), t == null || t.appendChild(a);
    })) : this.manuallyFilteredContainer.classList.add("hidden"));
  }
  getAvailableNodeAttributes() {
    const t = /* @__PURE__ */ new Map();
    this.uiManager.graph.getMutableNodes().forEach((r) => {
      Object.entries(r.getData()).forEach(([s, o]) => {
        let a = t.get(s);
        a || (a = {
          numbers: /* @__PURE__ */ new Set(),
          values: /* @__PURE__ */ new Set()
        }), Number.isInteger(o) ? a.range.add(o) : a.values.add(o), t.set(s, a);
      });
    });
    const n = /* @__PURE__ */ new Map();
    return t.forEach((r, s) => {
      const o = {};
      r.values ? o.values = [.../* @__PURE__ */ new Set([...r.values, ...r.numbers])] : r.number && (o.range = [Math.min(...r.numbers), Math.max(...r.numbers)]), n.set(s, o);
    }), Object.fromEntries(n);
  }
  filterGraph(t) {
    const e = this.getActiveFilters(t), n = {}, r = Object.fromEntries(this.formOptions.map((s) => [s.key, s]));
    for (const [s, o] of Object.entries(e)) {
      const a = {
        value: o,
        matchMode: r[s].matchMode
      };
      o !== void 0 && (n[s] = a);
    }
    this.uiManager.graph.queryEngine.resetFilters(), this.uiManager.graph.queryEngine.setFilters(n);
  }
  getActiveFilters(t) {
    const e = {};
    for (const [n, r] of Object.entries(t))
      this.isFilterActive(r) ? e[n] = r : e[n] = void 0;
    return e;
  }
  isFilterActive(t) {
    return t === void 0 ? !1 : typeof t == "string" ? t.trim() !== "" : typeof t == "number" || typeof t == "boolean" ? !0 : Array.isArray(t) ? t.length > 0 : typeof t == "object" ? t.min !== void 0 || t.max !== void 0 : !1;
  }
}
class dg {
  constructor(t) {
    f(this, "uiManager");
    f(this, "toolbar");
    f(this, "searchBoxButton");
    f(this, "filterButton");
    f(this, "undoButton");
    f(this, "redoButton");
    f(this, "filteringSlidepanel");
    f(this, "searchModal");
    this.uiManager = t;
  }
  mount(t) {
    if (!t) return;
    this.toolbar = document.createElement("div"), this.toolbar.className = "pvt-toolbar-elements";
    const e = document.createElement("template");
    e.innerHTML = `
  <div id="pvt-searchbox-button" class="pvt-action-button">
    <div class="action-container">
        <span class="icon-container">${Fs}</span>
        <span class="action-text">Search</span>
        <span class="pvt-keyboard-shortcut">Ctrl J</span>
    </div>
  </div>`, this.searchBoxButton = e.content.firstElementChild, this.toolbar.appendChild(this.searchBoxButton);
    const n = document.createElement("template");
    n.innerHTML = `
  <div id="pvt-filter-button" class="pvt-action-button">
    <div class="action-container">
        <span class="icon-container">${zs}</span>
        <span class="action-text">Filter Graph</span>
        <span class="pvt-keyboard-shortcut">Ctrl K</span>
    </div>
  </div>`, this.filterButton = n.content.firstElementChild;
    const r = document.createElement("template");
    r.innerHTML = `
  <div class="pvt-right">
    <div class="pvt-undoredo-group">
        <button id="pvt-undo-button" class="pvt-button-undo" disabled>
            ${Yu}
        </button>
        <button id="pvt-redo-button" class="pvt-button-redo" disabled>
            ${Xu}
        </button>
    </div>
  </div>`;
    const s = r.content.firstElementChild;
    s.prepend(this.filterButton), this.undoButton = s.querySelector("#pvt-undo-button") ?? void 0, this.redoButton = s.querySelector("#pvt-redo-button") ?? void 0, this.toolbar.appendChild(s), t.appendChild(this.toolbar);
  }
  destroy() {
    var t;
    (t = this.toolbar) == null || t.remove(), this.toolbar = void 0;
  }
  afterMount() {
    var e;
    if (!this.filterButton) return;
    this.uiManager.keyManager.register({ key: "Ctrl+j", callback: () => {
      var n;
      return (n = this.searchBoxButton) == null ? void 0 : n.click();
    } }), this.uiManager.keyManager.register({ key: "Ctrl+k", callback: () => {
      var n;
      return (n = this.filterButton) == null ? void 0 : n.click();
    } });
    const t = new hg(this.uiManager);
    this.filteringSlidepanel = this.uiManager.createSlidepanel({
      header: "Graph Filters",
      body: t.build()
    }), this.filterButton.addEventListener("click", () => {
      this.filteringSlidepanel.toggle();
    }), (e = this.searchBoxButton) == null || e.addEventListener("click", () => {
      var n, r;
      this.searchModal || (this.searchModal = this.uiManager.createModal({
        body: "",
        buttons: null,
        position: "top",
        size: "xl",
        noBodyPadding: !0
      }), this.searchModal && ((n = this.searchModal.modal) == null || n.addEventListener("pvt-modal-show", () => {
        var o, a, c, l;
        const s = new Cp(this.uiManager);
        (o = this.searchModal) == null || o.setBody(s.build()), (a = s.searchInput) == null || a.focus(), (c = s.searchBox) == null || c.addEventListener("pvt-searchbox-select", (h) => {
          var p;
          const u = h.detail;
          this.uiManager.graph.selectElement(u), (p = this.searchModal) == null || p.destroy();
        }), (l = s.searchBox) == null || l.addEventListener("pvt-searchbox-close", () => {
          var h;
          (h = this.searchModal) == null || h.destroy();
        });
      }), (r = this.searchModal.modal) == null || r.addEventListener("pvt-modal-hidden", () => {
        this.searchModal = void 0;
      })));
    });
  }
  graphReady() {
  }
}
class ug {
  constructor(t, e) {
    f(this, "uiManager");
    f(this, "options");
    f(this, "overlay");
    f(this, "modal");
    f(this, "header");
    f(this, "body");
    f(this, "footer");
    f(this, "DEFAULT_HEADER", null);
    f(this, "DEFAULT_BODY", "");
    f(this, "DEFAULT_BUTTON_CONFIG", {
      text: "Ok",
      variant: "primary",
      onClick: (t, e) => {
        e();
      }
    });
    this.uiManager = t, this.options = e, this.options.header || (this.options.header = this.DEFAULT_HEADER), this.options.body || (this.options.body = this.DEFAULT_BODY), !this.options.buttons && this.options.buttons !== null && (this.options.buttons = [this.DEFAULT_BUTTON_CONFIG]), this.options.position = e.position ?? "center";
  }
  mount(t) {
    if (!t) return;
    this.overlay = document.createElement("div"), this.overlay.className = "pvt-modal-overlay", this.overlay.classList.add(
      this.options.position === "center" ? "pvt-modal-overlay-center" : "pvt-modal-overlay-top"
    ), this.overlay.addEventListener("click", (n) => {
      n.target === this.overlay && this.destroy();
    }), this.modal = document.createElement("div"), this.modal.className = "pvt-modal";
    const e = this.options.size ?? "md";
    if (this.modal.classList.add(`pvt-modal-${e}`), this.options.header != null) {
      this.header = document.createElement("div"), this.header.className = "pvt-modal__header", this.setHeader(this.options.header), this.modal.appendChild(this.header);
      const n = ft({
        text: "×",
        variant: "outline-primary",
        size: "sm",
        onClick: () => {
          this.hide();
        },
        style: "margin-left: auto;"
      });
      this.header.appendChild(n);
    }
    this.body = document.createElement("div"), this.body.className = "pvt-modal__body", this.setBody(this.options.body), this.options.noBodyPadding ? this.body.style.padding = "0" : this.body.style.padding = "", this.modal.appendChild(this.body), this.options.buttons != null && (this.footer = document.createElement("div"), this.footer.className = "pvt-modal__footer", this.setButtons(this.options.buttons), this.modal.appendChild(this.footer)), this.overlay.appendChild(this.modal), t.appendChild(this.overlay);
  }
  destroy() {
    this.hide(), requestAnimationFrame(() => {
      var t;
      (t = this.overlay) == null || t.remove(), this.overlay = void 0;
    });
  }
  afterMount() {
  }
  graphReady() {
  }
  setButtons(t) {
    !this.modal || !this.footer || (this.footer.innerHTML = "", t.forEach((e) => {
      if (typeof e.onClick == "function") {
        const r = e.onClick;
        e.onClick = (s, o) => {
          r && r(s, o);
        }, e.onClickArgs = [this.hide.bind(this)];
      }
      const n = ft(e);
      this.footer.appendChild(n);
    }));
  }
  setHeader(t) {
    this.header && (this.header.innerHTML = "", t && (this.options.header instanceof HTMLElement ? this.header.appendChild(this.options.header) : this.options.rawHeader ? this.header.innerHTML = this.options.header : this.header.textContent = this.options.header));
  }
  setBody(t) {
    this.body && (this.body.innerHTML = "", t && (t instanceof HTMLElement ? this.body.appendChild(t) : this.options.rawBody ? this.body.innerHTML = t : this.body.textContent = t));
  }
  show() {
    if (!this.modal || !this.overlay) return;
    this.dispatchEvent("show"), this.modal.classList.add("pvt-modal-open");
    const t = (e) => {
      var n;
      e.target === this.modal && ((n = this.modal) == null || n.removeEventListener("animationend", t), this.dispatchEvent("shown"));
    };
    this.modal.addEventListener("animationend", t);
  }
  hide() {
    var t;
    !this.modal || !this.overlay || (this.dispatchEvent("hide"), this.modal.classList.remove("pvt-modal-open"), (t = this.overlay) == null || t.remove(), requestAnimationFrame(() => {
      this.dispatchEvent("hidden");
    }));
  }
  dispatchEvent(t) {
    if (!this.modal) return;
    const e = `pvt-modal-${t}`, n = new CustomEvent(e, { bubbles: !0, cancelable: !0 });
    this.modal.dispatchEvent(n);
    const r = `on${t.charAt(0).toUpperCase()}${t.slice(1)}`, s = this.options[r];
    typeof s == "function" && s();
  }
}
const pg = {
  enabled: !0,
  allowPinning: !0
};
class fg {
  constructor(t) {
    f(this, "uiManager");
    f(this, "options");
    f(this, "tooltip");
    f(this, "parentContainer");
    f(this, "shadowLinkContainer");
    f(this, "mouseX", 0);
    f(this, "mouseY", 0);
    f(this, "x", 0);
    f(this, "y", 0);
    f(this, "triggerX", 0);
    f(this, "triggerY", 0);
    f(this, "hoveredElementID", null);
    f(this, "hoveredElement", null);
    f(this, "showDelay", 400);
    f(this, "hideDelay", 200);
    f(this, "tooltipTimeout", null);
    f(this, "hideTimeout", null);
    f(this, "tooltipDataMap", /* @__PURE__ */ new Map());
    f(this, "shadowlinkMap", /* @__PURE__ */ new WeakMap());
    f(this, "shadowlinkBoundingBoxesMap", /* @__PURE__ */ new WeakMap());
    this.uiManager = t, this.options = se(pg, this.uiManager.getOptions().tooltip);
  }
  mount(t) {
    if (!t) return;
    this.parentContainer = document.querySelector("body");
    const e = this.parentContainer.querySelector(".pvt-tooltip"), n = this.parentContainer.querySelector(".pivotick-shadowlink-container");
    if (e && n) {
      this.tooltip = e, this.shadowLinkContainer = n;
      return;
    }
    const r = document.createElement("template");
    r.innerHTML = '<div class="pvt-tooltip"></div>', this.tooltip = r.content.firstElementChild, this.shadowLinkContainer = document.createElementNS("http://www.w3.org/2000/svg", "svg"), this.shadowLinkContainer.setAttribute("class", "pivotick-shadowlink-container"), this.parentContainer.appendChild(this.tooltip), this.parentContainer.appendChild(this.shadowLinkContainer);
  }
  destroy() {
    var t;
    (t = this.tooltip) == null || t.remove(), this.tooltip = void 0;
  }
  afterMount() {
  }
  graphReady() {
    this.tooltip && (this.uiManager.graph.renderer.getGraphInteraction().on("nodeHoverIn", this.nodeHovered.bind(this)), this.uiManager.graph.renderer.getGraphInteraction().on("nodeHoverOut", this.delayedHide.bind(this)), this.uiManager.graph.renderer.getGraphInteraction().on("canvasMousemove", this.updateMousePosition.bind(this)), this.uiManager.graph.renderer.getGraphInteraction().on("dragging", (t, e) => {
      this.hoveredElementID === e.id && this.hide(e);
    }), this.uiManager.graph.renderer.getGraphInteraction().on("canvasZoom", this.canvasZoomed.bind(this)), this.uiManager.graph.renderer.getGraphInteraction().on("simulationSlowTick", this.simulationSlowTick.bind(this)), this.tooltip.addEventListener("mouseenter", () => {
      this.hideTimeout && (clearTimeout(this.hideTimeout), this.hideTimeout = null);
    }), this.tooltip.addEventListener("mouseleave", () => this.hide()));
  }
  updateMousePosition(t) {
    this.mouseX = t.pageX, this.mouseY = t.pageY;
  }
  tooltipCanBeShown() {
    if (!this.tooltip || this.uiManager.graph.simulation.isDragging()) return !1;
    const t = this.uiManager.graph.renderer.getSelectionBox();
    return !(t !== null && t.selectionInProgress() || Math.abs(this.triggerX - this.mouseX) >= 50 || Math.abs(this.triggerY - this.mouseY) >= 50);
  }
  openForNodeOnElement(t, e) {
    this.triggerX = t.pageX, this.triggerY = t.pageY, this.mouseY = t.pageY, this.mouseX = t.pageX, this.hoveredElementID = e.id, this.hoveredElement = e, this.tooltipCanBeShown() && this.show(() => {
      this.createNodeTooltip(e);
    });
  }
  nodeHovered(t, e) {
    this.hoveredElementID !== e.id && (this.triggerX = t.pageX, this.triggerY = t.pageY, this.hoveredElementID = e.id, this.hoveredElement = e, this.tooltipCanBeShown() && this.show(() => {
      this.createNodeTooltip(e);
    }));
  }
  edgeHovered(t, e) {
    this.hoveredElementID !== e.id && (this.triggerX = t.pageX, this.triggerY = t.pageY, this.hoveredElementID = e.id, this.hoveredElement = e, this.tooltipCanBeShown() && this.show(() => {
      if (this.uiManager.graph.simulation.isDragging()) {
        this.hide();
        return;
      }
      this.createEdgeTooltip(e);
    }));
  }
  canvasZoomed() {
    this.updateShadowLinks(!0);
  }
  simulationSlowTick() {
    this.updateShadowLinks(!0);
  }
  buildNodeTooltip(t) {
    var v;
    const r = ot(`
<div class="pvt-tooltip-container">
    <div class="pvt-mainheader-container">
        <div class="pvt-mainheader-nodepreview">
            <svg class="pvt-mainheader-icon" width="32" height="32" viewBox="0 0 32 32" preserveAspectRatio="xMidYMid meet"></svg>
            <span class="pvt-mainheader-topright"></span>
        </div>
        <div class="pvt-mainheader-nodeinfo">
            <div class="pvt-mainheader-nodeinfo-name"></div>
            <div class="pvt-mainheader-nodeinfo-subtitle"></div>
        </div>
        <div class="pvt-mainheader-nodeinfo-action">
        </div>
    </div>
</div>`), s = r.querySelector(".pvt-mainheader-container"), o = r.querySelector(".pvt-mainheader-icon"), a = r.querySelector(".pvt-mainheader-nodeinfo-name"), c = r.querySelector(".pvt-mainheader-nodeinfo-subtitle"), l = r.querySelector(".pvt-mainheader-topright"), h = gn(t, this.uiManager.getOptions().propertiesPanel), d = t.getGraphElement();
    if (d && d instanceof SVGGElement) {
      const y = d.cloneNode(!0);
      (v = y.querySelector("circle.pvt-node-selected-highlight")) == null || v.remove();
      const b = d.getBBox(), x = 32 / Math.max(b.width, b.height);
      y.setAttribute(
        "transform",
        `translate(${(32 - b.width * x) / 2 - b.x * x}, ${(32 - b.height * x) / 2 - b.y * x}) scale(${x})`
      ), o.appendChild(y);
    }
    if (a.textContent = Wt(t, this.uiManager.getOptions().mainHeader), c.textContent = As(t, this.uiManager.getOptions().mainHeader), this.options.allowPinning) {
      const y = ft({
        title: "Pin Tooltip",
        variant: "outline-primary",
        size: "sm",
        class: "pin-button",
        svgIcon: le,
        onClick: () => {
          this.pinTooltip();
        }
      });
      l.appendChild(y);
    }
    const u = this.uiManager.getOptions().tooltip.render;
    if (u && typeof u == "function") {
      const y = St(u, t);
      if (y) {
        const b = T("div", { class: "pivotick-extra-content-container" }, [
          y
        ]);
        r.appendChild(b);
      }
      return r;
    }
    const p = T("div", { class: "pvt-properties-container" }, [
      si(h, t)
    ]);
    r.appendChild(s), r.appendChild(p);
    const g = this.uiManager.getOptions().tooltip.renderNodeExtra;
    if (g && typeof g == "function") {
      const y = St(g, t);
      if (y) {
        const b = T("div", { class: "pivotick-extra-content-container" }, [
          y
        ]);
        r.appendChild(b);
      }
    }
    return r;
  }
  createNodeTooltip(t) {
    if (!this.tooltip) return !1;
    this.tooltip.innerHTML = "";
    const e = this.buildNodeTooltip(t);
    this.tooltip.appendChild(e);
  }
  createEdgeTooltip(t) {
    if (!this.tooltip) return !1;
    this.tooltip.innerHTML = "";
    const n = `
<div class="pvt-tooltip-container">
    <div class="pvt-mainheader-container">
        <div class="pvt-mainheader-nodepreview">
            ${pi(32)}
            <span class="pvt-mainheader-topright"></span>
        </div>
        <div class="pvt-mainheader-nodeinfo">
            <div class="pvt-mainheader-nodeinfo-name"></div>
            <div class="pvt-mainheader-nodeinfo-subtitle"></div>
        </div>
        <div class="pvt-mainheader-nodeinfo-action">
        </div>
    </div>
</div>`, r = ot(n), s = r.querySelector(".pvt-mainheader-container"), o = r.querySelector(".pvt-mainheader-nodeinfo-name"), a = r.querySelector(".pvt-mainheader-nodeinfo-subtitle"), c = r.querySelector(".pvt-mainheader-topright"), l = ft({
      title: "Pin Tooltip",
      variant: "outline-primary",
      size: "sm",
      class: "pin-button",
      svgIcon: le,
      onClick: () => {
        this.pinTooltip();
      }
    });
    c.appendChild(l);
    const h = this.uiManager.getOptions().tooltip.render;
    if (h && typeof h == "function") {
      const g = St(h, t);
      if (g) {
        const v = T("div", { class: "pivotick-extra-content-container" }, [
          g
        ]);
        r.appendChild(v);
      }
      this.tooltip.appendChild(r);
      return;
    }
    const d = mn(t, this.uiManager.getOptions().propertiesPanel);
    o.textContent = be(t, this.uiManager.getOptions().mainHeader), a.textContent = Is(t, this.uiManager.getOptions().mainHeader);
    const u = T("div", { class: "pvt-properties-container" }, [si(d, t)]);
    r.appendChild(s), r.appendChild(u);
    const p = this.uiManager.getOptions().tooltip.renderEdgeExtra;
    if (p && typeof p == "function") {
      const g = St(p, t);
      if (g) {
        const v = T("div", { class: "pivotick-extra-content-container" }, [
          g
        ]);
        r.appendChild(v);
      }
    }
    this.tooltip.appendChild(r);
  }
  setPosition() {
    var d, u, p, g;
    if (!this.tooltip) return;
    const t = (u = (d = this.hoveredElement) == null ? void 0 : d.getGraphElement()) == null ? void 0 : u.getBoundingClientRect();
    if (!t) return;
    const e = (g = (p = this.uiManager.layout) == null ? void 0 : p.canvas) == null ? void 0 : g.getBoundingClientRect();
    if (!e) return;
    const n = 20, r = 15, s = e.left + window.scrollX, o = e.top + window.scrollY, a = e.width, c = e.height, l = this.tooltip.offsetWidth, h = this.tooltip.offsetHeight;
    this.x = t.x + t.width + r, this.y = t.y, this.x + l + n > s + a && (this.x = t.x - l - r), this.x < s + r && (this.x = s + r), this.y + h + n > o + c && (this.y -= h), this.y < o + n && (this.y = o + n), this.tooltip.style.left = `${this.x}px`, this.tooltip.style.top = `${this.y}px`;
  }
  delayedHide(t, e) {
    this.hideTimeout && clearTimeout(this.hideTimeout), this.hideTimeout = setTimeout(() => this.hide(e), this.hideDelay);
  }
  hide(t) {
    this.tooltip && (this.hideTimeout && clearTimeout(this.hideTimeout), (this.hoveredElement === t || t === void 0) && (this.tooltipTimeout && (clearTimeout(this.tooltipTimeout), this.tooltipTimeout = null), this.hoveredElementID = null, this.hoveredElement = null, this.triggerX = -2e3, this.triggerY = -2e3, this.tooltip.classList.remove("shown"), this.tooltip.style.left = "-10000px"));
  }
  show(t) {
    var e;
    (e = this.uiManager.contextMenu) != null && e.visible || (this.tooltipTimeout && clearTimeout(this.tooltipTimeout), this.tooltipTimeout = setTimeout(() => {
      var n;
      t && t(), (n = this.tooltip) == null || n.classList.add("shown"), requestAnimationFrame(() => {
        this.setPosition();
      });
    }, this.showDelay));
  }
  pinTooltip() {
    var a;
    if (!this.tooltip || !this.parentContainer || !this.hoveredElement) return;
    const t = this.tooltip.cloneNode(!0);
    this.tooltipDataMap.set(t, this.hoveredElement), t.classList.add("pvt-tooltip-floating"), (a = t.querySelector(".pin-button")) == null || a.remove();
    const e = ft({
      title: "Close Tooltip",
      variant: "outline-danger",
      size: "sm",
      class: ["close-button"],
      svgIcon: tp,
      onClick: () => {
        this.tooltipDataMap.delete(t), this.reomveShadowLink(t), t.remove();
      }
    }), n = ft({
      title: "Focus Element in Graph",
      variant: "outline-primary",
      size: "sm",
      class: ["focus-element"],
      svgIcon: Bs,
      onClick: () => {
        const c = this.tooltipDataMap.get(t);
        c && this.uiManager.graph.focusElement(c);
      }
    }), r = ft({
      title: "Select Element in Graph",
      variant: "outline-primary",
      size: "sm",
      class: ["select-element"],
      svgIcon: ep,
      onClick: () => {
        const c = this.tooltipDataMap.get(t);
        c && this.uiManager.graph.selectElement(c);
      }
    }), s = T("div", {
      class: "pvt-tooltip-topbar"
    }, [
      n,
      r,
      e
    ]);
    t.prepend(s);
    const o = this.uiManager.getAppContainer();
    va(t, s, o, {
      onDragStart: (c, l) => {
        this.shadowlinkBoundingBoxesMap.set(l, [
          l.getBoundingClientRect(),
          this.tooltipDataMap.get(l).getGraphElement().getBoundingClientRect()
        ]);
      },
      onDrag: (c, l) => {
        this.updateShadowLink(l, this.tooltipDataMap.get(l));
      }
    }), this.parentContainer.appendChild(t), this.addShadowLink(t);
  }
  addShadowLink(t) {
    var n;
    const e = fa("path", {
      class: "pivotick-shadowlink"
    });
    this.shadowlinkMap.set(t, e), (n = this.shadowLinkContainer) == null || n.appendChild(e);
  }
  updateShadowLinks(t = !1) {
    for (const [e, n] of this.tooltipDataMap.entries())
      this.updateShadowLink(e, n, t);
  }
  updateShadowLink(t, e, n = !1) {
    let r;
    n ? r = [
      t.getBoundingClientRect(),
      e.getGraphElement().getBoundingClientRect()
    ] : r = this.shadowlinkBoundingBoxesMap.get(t);
    const { width: s, height: o } = r[0], { x: a, y: c, width: l, height: h } = r[1], d = this.shadowlinkMap.get(t), u = parseFloat(t.style.left), p = parseFloat(t.style.top);
    d && d.setAttribute("d", `M ${u + s / 2} ${p + o / 2} L ${a + l / 2} ${c + h / 2}`);
  }
  reomveShadowLink(t) {
    const e = this.shadowlinkMap.get(t);
    e && e.remove();
  }
}
const gg = {
  topbar: [
    {
      title: "Pin Node",
      svgIcon: le,
      variant: "outline-primary",
      visible: (i) => !i.frozen,
      onclick(i, t) {
        t.freeze();
      }
    },
    {
      title: "Unpin Node",
      svgIcon: Pn,
      variant: "outline-primary",
      visible: (i) => i.frozen,
      onclick(i, t) {
        t.unfreeze();
      }
    },
    {
      title: "Focus Node",
      svgIcon: Bs,
      variant: "outline-primary",
      onclick(i, t) {
        this.uiManager.graph.focusElement(t);
      }
    },
    {
      title: "Hide Node",
      svgIcon: vn,
      variant: "outline-danger",
      flushRight: !0,
      visible: (i) => i.visible,
      onclick(i, t) {
        this.uiManager.graph.queryEngine.excludeNode(t);
      }
    }
  ],
  menu: [
    {
      text: "Select Neighbors",
      title: "Select Neighbors",
      svgIcon: Uu,
      variant: "outline-primary",
      onclick(i, t) {
        const e = [
          ...t.getConnectedNodes(),
          ...t.getConnectingNodes()
        ].map((n) => ({
          node: n,
          element: n.getGraphElement()
        }));
        this.uiManager.graph.renderer.getGraphInteraction().selectNodes(e);
      }
    },
    {
      text: "Hide Children",
      title: "Hide Children",
      svgIcon: vn,
      variant: "outline-primary",
      visible: (i) => i.visible,
      onclick(i, t) {
        t.hide();
      }
    },
    {
      text: "Expand Node",
      title: "Expand Node",
      svgIcon: Rs,
      variant: "outline-primary",
      // eslint-disable-next-line @typescript-eslint/no-unused-vars
      visible: (i) => !1,
      // eslint-disable-next-line @typescript-eslint/no-unused-vars
      onclick(i, t) {
      }
    },
    {
      text: "Inspect Properties",
      title: "Inspect Properties",
      svgIcon: ip,
      variant: "outline-primary",
      // eslint-disable-next-line @typescript-eslint/no-unused-vars
      visible: (i) => !0,
      onclick(i, t) {
        this.uiManager.graph.renderer.getGraphInteraction().selectNode(t.getGraphElement(), t);
      }
    }
  ]
}, mg = {
  topbar: [],
  menu: []
}, vg = {
  topbar: [
    {
      title: "Pin All",
      svgIcon: le,
      variant: "outline-primary",
      visible: !0,
      // eslint-disable-next-line @typescript-eslint/no-unused-vars
      onclick(i) {
        (this.uiManager.graph.getMutableNodes() ?? []).forEach((e) => {
          e.freeze();
        });
      }
    },
    {
      title: "Unpin All",
      svgIcon: Pn,
      variant: "outline-primary",
      visible: !0,
      // eslint-disable-next-line @typescript-eslint/no-unused-vars
      onclick(i) {
        var e;
        (this.uiManager.graph.getMutableNodes() ?? []).forEach((n) => {
          n.unfreeze();
        }), (e = this.uiManager.graph.simulation) == null || e.reheat();
      }
    }
  ],
  menu: []
};
class yg {
  constructor(t) {
    f(this, "uiManager");
    f(this, "menu");
    f(this, "visible");
    f(this, "parentContainer");
    f(this, "element", null);
    f(this, "menuNode");
    f(this, "menuEdge");
    f(this, "menuCanvas");
    this.uiManager = t, this.visible = !1, this.menuNode = se(gg, this.uiManager.getOptions().contextMenu.menuNode ?? {}), this.menuEdge = se(mg, this.uiManager.getOptions().contextMenu.menuEdge ?? {}), this.menuCanvas = se(vg, this.uiManager.getOptions().contextMenu.menuCanvas ?? {}), this.wrapOnclickActions();
  }
  mount(t) {
    if (!t) return;
    this.parentContainer = document.querySelector("body");
    const e = this.parentContainer.querySelector(".pvt-contextmenu");
    if (e) {
      this.menu = e;
      return;
    }
    const n = document.createElement("template");
    n.innerHTML = `
        <div class="pvt-contextmenu">
            <div class="pvt-contextmenu-topbar"></div>
            <div class="pvt-contextmenu-mainmenu"></div>
        </div>
        `, this.menu = n.content.firstElementChild, this.parentContainer.appendChild(this.menu);
  }
  destroy() {
    var t;
    (t = this.menu) == null || t.remove(), this.menu = void 0;
  }
  afterMount() {
  }
  graphReady() {
    this.uiManager.graph.renderer.getGraphInteraction().on("nodeContextmenu", this.nodeClicked.bind(this)), this.uiManager.graph.renderer.getGraphInteraction().on("edgeContextmenu", this.edgeClicked.bind(this)), this.uiManager.graph.renderer.getGraphInteraction().on("canvasContextmenu", this.canvasClicked.bind(this)), this.uiManager.graph.renderer.getGraphInteraction().on("canvasClick", () => {
      this.hide();
    }), this.uiManager.graph.renderer.getGraphInteraction().on("canvasZoom", () => {
      this.hide();
    });
  }
  nodeClicked(t, e) {
    this.menu && (this.element = e, this.createNodeMenu(e), this.setPosition(t), this.show());
  }
  edgeClicked(t, e) {
    this.menu && (this.element = e, this.createEdgeMenu(e), this.setPosition(t), this.show());
  }
  canvasClicked(t) {
    this.menu && (this.element = null, this.createCanvasMenu(), this.setPosition(t), this.show());
  }
  wrapOnclickActions() {
    [
      this.menuNode.menu,
      this.menuNode.topbar,
      this.menuEdge.menu,
      this.menuEdge.topbar,
      this.menuCanvas.menu,
      this.menuCanvas.topbar
    ].forEach((t) => {
      t.forEach((e) => {
        this.wrapOnclickAction(e);
      });
    });
  }
  wrapOnclickAction(t) {
    if (t.onclick) {
      const e = t.onclick, n = this;
      t.onclick = function(r, s) {
        var o;
        e.apply(this, [r, s]), (o = n.hide) == null || o.call(n);
      };
    }
  }
  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  createNodeMenu(t) {
    if (!this.menu) return;
    const e = this.menu.querySelector(".pvt-contextmenu-topbar"), n = this.menu.querySelector(".pvt-contextmenu-mainmenu");
    e.innerHTML = "", n.innerHTML = "", e.appendChild(We(this, this.menuNode.topbar, this.element)), n.appendChild(Ke(this, this.menuNode.menu, this.element));
  }
  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  createEdgeMenu(t) {
    if (!this.menu) return;
    const e = this.menu.querySelector(".pvt-contextmenu-topbar"), n = this.menu.querySelector(".pvt-contextmenu-mainmenu");
    e.innerHTML = "", n.innerHTML = "", e.appendChild(We(this, this.menuEdge.topbar, this.element)), n.appendChild(Ke(this, this.menuEdge.menu, this.element));
  }
  createCanvasMenu() {
    if (!this.menu) return;
    const t = this.menu.querySelector(".pvt-contextmenu-topbar"), e = this.menu.querySelector(".pvt-contextmenu-mainmenu");
    t.innerHTML = "", e.innerHTML = "", t.appendChild(We(this, this.menuCanvas.topbar, this.element)), e.appendChild(Ke(this, this.menuCanvas.menu, this.element));
  }
  show() {
    var t;
    this.visible || this.menu && ((t = this.uiManager.tooltip) == null || t.hide(), this.menu.classList.add("shown"), this.visible = !0);
  }
  hide() {
    this.visible && this.menu && (this.element = null, this.menu.classList.remove("shown"), this.menu.style.left = "-10000px", this.visible = !1);
  }
  setPosition(t) {
    if (!this.menu) return;
    const e = 10, n = t.pageX, r = t.pageY;
    this.menu.style.left = `${n + e}px`, this.menu.style.top = `${r + e}px`;
  }
}
class bg {
  constructor() {
    f(this, "bindings", /* @__PURE__ */ new Map());
  }
  register(t) {
    this.bindings.set(t.key, t.callback);
  }
  handleKeyPress(t) {
    const e = this.getKeyCombo(t), n = this.bindings.get(e);
    n && (t.preventDefault(), n(t));
  }
  getKeyCombo(t) {
    const e = [];
    return t.ctrlKey && e.push("Ctrl"), t.shiftKey && e.push("Shift"), t.altKey && e.push("Alt"), e.push(t.key), e.join("+");
  }
}
const Ks = (i) => {
  const t = [];
  for (const [e, n] of Object.entries(i.getData()))
    e && n && t.push({
      name: e,
      value: n
    });
  return t;
}, Mi = (i, t, e = "") => {
  var r;
  const n = (r = i.getData()) == null ? void 0 : r[t];
  return typeof n == "string" ? n : e;
}, wg = (i) => Mi(i, "label", "Could not resolve title"), xg = (i) => Mi(i, "description"), Cg = (i) => Mi(i, "label", ""), Mg = (i) => Mi(i, "description"), Kr = (i) => Ks(i), Zr = (i) => Ks(i), Qr = {
  nodeHeaderMap: {
    title: wg,
    subtitle: xg
  },
  edgeHeaderMap: {
    title: Cg,
    subtitle: Mg
  },
  render: void 0
}, Eg = {
  mode: "viewer",
  mainHeader: Qr,
  sidebar: {
    collapsed: "auto"
  },
  propertiesPanel: {
    nodePropertiesMap: Kr,
    edgePropertiesMap: Zr
  },
  neighborsPanel: {},
  tooltip: {
    enabled: !0,
    allowPinning: !0,
    nodePropertiesMap: Kr,
    edgePropertiesMap: Zr,
    ...Qr
  },
  navigation: {
    enabled: !0
  },
  contextMenu: {
    enabled: !0,
    menuNode: {
      topbar: [],
      menu: []
    },
    menuEdge: {
      topbar: [],
      menu: []
    },
    menuCanvas: {
      topbar: [],
      menu: []
    }
  },
  selectionMenu: {
    menuNode: {
      topbar: [],
      menu: []
    }
  },
  extraPanels: []
};
class Sg {
  constructor(t, e, n) {
    f(this, "graph");
    f(this, "container");
    f(this, "options");
    f(this, "layout");
    f(this, "slidePanel");
    f(this, "sidebar");
    f(this, "toolbar");
    f(this, "modal");
    f(this, "graphNaviation");
    f(this, "graphControls");
    f(this, "tooltip");
    f(this, "contextMenu");
    f(this, "keyManager");
    this.graph = t, this.container = e, this.options = re({}, Eg, n), this.keyManager = new bg(), this.setup();
  }
  setup() {
    switch (this.destroy(), this.options.mode) {
      case "viewer":
        this.setupViewerMode();
        break;
      case "full":
        this.setupFullMode();
        break;
      case "light":
        this.setupLightMode();
        break;
      case "static":
        this.setupStaticMode();
        break;
      default:
        console.warn(`Unknown mode: ${this.options.mode}. Defaulting to 'viewer'.`), this.setupViewerMode();
        break;
    }
    this.callAfterMount();
  }
  hasEnoughSpaceForFullMode() {
    const t = this.container.getBoundingClientRect();
    return t.width > 1200 && t.height > 800;
  }
  hasEnoughSpaceForLightMode() {
    const t = this.container.getBoundingClientRect();
    return t.width > 600 && t.height > 600;
  }
  setupViewerMode() {
    this.buildLayout(), this.buildUIGraphNavigation();
  }
  setupStaticMode() {
    this.buildLayout();
  }
  setupFullMode() {
    var t, e;
    ((e = (t = this.options) == null ? void 0 : t.sidebar) == null ? void 0 : e.collapsed) === "auto" && !this.hasEnoughSpaceForFullMode() && (console.debug("Not enough space for full mode UI. Collapsing sidebar"), this.options.sidebar.collapsed = !0), this.buildLayout(), this.buildUIGraphNavigation(), this.buildUIGraphControls(), this.buildToolbar(), this.buildSidebar();
  }
  setupLightMode() {
    if (!this.hasEnoughSpaceForLightMode()) {
      console.warn("Not enough space for light mode UI. Switching to viewer mode."), this.options.mode = "viewer", this.setupViewerMode();
      return;
    }
    this.buildLayout(), this.buildUIGraphNavigation(), this.buildUIGraphControls(), this.buildToolbar();
  }
  buildLayout() {
    this.layout = new cp(), this.layout.mount(this.container, this.options.mode);
  }
  buildUIGraphNavigation() {
    var t, e, n, r, s;
    this.options.navigation.enabled && (this.graphNaviation = new lp(this), this.graphNaviation.mount((t = this.layout) == null ? void 0 : t.graphnavigation)), (e = this.options.tooltip) != null && e.enabled && (this.tooltip = new fg(this), this.tooltip.mount((n = this.layout) == null ? void 0 : n.canvas)), (r = this.options.contextMenu) != null && r.enabled && (this.contextMenu = new yg(this), this.contextMenu.mount((s = this.layout) == null ? void 0 : s.canvas));
  }
  buildUIGraphControls() {
    var t;
    this.graphControls = new ap(this), this.graphControls.mount((t = this.layout) == null ? void 0 : t.graphcontrols);
  }
  buildToolbar() {
    var t;
    this.toolbar = new dg(this), this.toolbar.mount((t = this.layout) == null ? void 0 : t.toolbar);
  }
  buildSidebar() {
    var t;
    this.sidebar = new wp(this), this.sidebar.mount((t = this.layout) == null ? void 0 : t.sidebar);
  }
  destroy() {
    this.layout && (this.layout.destroy(), this.layout = void 0);
  }
  callAfterMount() {
    var t, e, n, r, s, o, a, c, l;
    (t = this.layout) == null || t.afterMount(), (e = this.toolbar) == null || e.afterMount(), (n = this.sidebar) == null || n.afterMount(), (r = this.graphNaviation) == null || r.afterMount(), (s = this.graphControls) == null || s.afterMount(), (o = this.options.tooltip) != null && o.enabled && ((a = this.tooltip) == null || a.afterMount()), (c = this.options.contextMenu) != null && c.enabled && ((l = this.contextMenu) == null || l.afterMount()), this.container.addEventListener("keydown", (h) => this.keyManager.handleKeyPress(h)), this.container.setAttribute("tabindex", "0");
  }
  getOptions() {
    return this.options;
  }
  getAppContainer() {
    const t = this.graph.getAppID();
    return document.getElementById(t);
  }
  callGraphReady() {
    var t, e, n, r;
    (t = this.graphControls) == null || t.graphReady(), (e = this.sidebar) == null || e.graphReady(), (n = this.tooltip) == null || n.graphReady(), (r = this.contextMenu) == null || r.graphReady();
  }
  /**
  * Show a notification in the UI.
  * 
  * @param notification - The notification to display
  */
  showNotification(t) {
    var h;
    const { level: e, title: n, message: r } = t, s = (h = this.layout) == null ? void 0 : h.notification;
    if (!s) return;
    const o = document.createElement("template");
    o.innerHTML = `
  <div class="pivotick-toast pivotick-toast-${e}">
    <div class="pivotick-toast-title">
    </div>
    <div class="pivotick-toast-body">
    </div>
  </div>
`;
    const a = o.content.firstElementChild, c = a.querySelector(".pivotick-toast-title"), l = a.querySelector(".pivotick-toast-body");
    c && (c.textContent = n), l && (l.textContent = r ?? ""), s.appendChild(a), requestAnimationFrame(() => {
      a.classList.add("show");
    }), setTimeout(() => {
      a.classList.remove("show"), a.addEventListener("transitionend", () => {
        a.remove();
      }, { once: !0 });
    }, 4e3);
  }
  /**
  * Show a modal in the UI.
  * 
  * @param modalOption - The option for the modal
  */
  createModal(t) {
    var r, s;
    if (!((r = this.layout) == null ? void 0 : r.modal)) return;
    const n = new ug(this, t);
    return n.mount((s = this.layout) == null ? void 0 : s.modal), requestAnimationFrame(() => {
      n.show();
    }), n;
  }
  /**
  * Show a sidepanel in the UI.
  * 
  * @param slidepanelOption - The notification to display
  */
  createSlidepanel(t) {
    var r, s;
    if (!((r = this.layout) == null ? void 0 : r.slidePanel)) return;
    const n = new xp(this, t);
    return n.mount((s = this.layout) == null ? void 0 : s.slidePanel), n;
  }
}
const Xe = {
  Success: "success",
  Warning: "warning",
  Danger: "danger",
  Info: "info"
};
class _g {
  constructor(t) {
    f(this, "graph");
    f(this, "UIManager");
    this.graph = t, this.UIManager = this.graph.UIManager;
  }
  /**
   * Dispatch a notification to the UIManager.
   * 
   * @param level - The severity level of the notification.
   * @param title - The title to display in the notification.
   * @param message - Optional detailed message for the notification.
   */
  notify(t, e, n) {
    const r = { level: t, title: e, message: n };
    this.UIManager.showNotification(r);
  }
  success(t, e) {
    this.notify(Xe.Success, t, e);
  }
  warning(t, e) {
    this.notify(Xe.Warning, t, e);
  }
  error(t, e) {
    this.notify(Xe.Danger, t, e);
  }
  info(t, e) {
    this.notify(Xe.Info, t, e);
  }
}
const rn = "manually_hidden";
class kg {
  constructor(t) {
    f(this, "graph");
    f(this, "listeners");
    f(this, "filters", {});
    f(this, "excludedNodeIds", /* @__PURE__ */ new Set());
    f(this, "hiddenNodeCount", 0);
    this.graph = t, this.listeners = {
      filterAdd: [],
      filterRemove: [],
      filterReset: [],
      filterChange: []
    };
  }
  on(t, e) {
    this.listeners[t].push(e);
  }
  off(t, e) {
    this.listeners[t] = this.listeners[t].filter((n) => n !== e);
  }
  emit(t, ...e) {
    for (const n of this.listeners[t])
      n(...e);
  }
  getFilters() {
    const t = {
      value: [...this.excludedNodeIds],
      matchMode: "exact"
    };
    return { ...this.filters, manuallyHidden: t };
  }
  setFilters(t) {
    for (const [e, n] of Object.entries(t)) {
      if (n === void 0) {
        this.removeFilter(e);
        return;
      }
      this.filters[e] = n;
    }
    this.apply(), this.emit("filterChange", this.getFilters());
  }
  setFilter(t, e) {
    if (e === void 0) {
      this.removeFilter(t);
      return;
    }
    this.filters[t] = e, this.apply(), this.emit("filterAdd", t, e), this.emit("filterChange", this.getFilters());
  }
  removeFilter(t) {
    t in this.filters && (delete this.filters[t], this.apply(), this.emit("filterRemove", t), this.emit("filterChange", this.getFilters()));
  }
  resetFilters() {
    this.filters = {}, this.apply(), this.emit("filterReset"), this.emit("filterChange", this.getFilters());
  }
  excludeNode(t) {
    let e;
    if (t instanceof Mt ? e = t : e = this.graph.getNode(t), e === void 0) return;
    this.excludedNodeIds.add(e.id), this.hiddenNodeCount++;
    const n = {
      value: e.id,
      matchMode: "exact"
    };
    this.graph.hideNode(e), this.emit("filterAdd", rn, n), this.emit("filterChange", this.getFilters());
  }
  includeNode(t) {
    let e;
    t instanceof Mt ? e = t : e = this.graph.getNode(t), e !== void 0 && (this.excludedNodeIds.delete(e.id), this.hiddenNodeCount--, this.graph.showNode(e), this.emit("filterRemove", rn), this.emit("filterChange", this.getFilters()));
  }
  clearNodeExclusions() {
    this.hiddenNodeCount += this.excludedNodeIds.size, this.excludedNodeIds.clear(), this.apply(), this.emit("filterRemove", rn), this.emit("filterChange", this.getFilters());
  }
  getExcludedNodeCount() {
    return this.excludedNodeIds.size;
  }
  getExcludedNodes() {
    return [...this.excludedNodeIds].map((t) => this.graph.getMutableNode(t)).filter((t) => t !== void 0);
  }
  getHiddenNodeCount() {
    return this.hiddenNodeCount;
  }
  apply() {
    const t = this.graph.getMutableNodes(), n = t.filter((r) => this.nodeMatchesFilters(r)).filter((r) => r.childrenDepth === 0);
    this.hiddenNodeCount = t.length - n.length, this.applyFiltersOnSubgraph(), this.graph.setVisibleNodes(n);
  }
  applyFiltersOnSubgraph() {
    const t = this.getFilters();
    this.graph.getMutableNodes().filter((e) => e.childrenDepth === 0).forEach((e) => {
      const n = e.getSubgraph();
      e.isParent && n && (n.queryEngine.resetFilters(), n.queryEngine.setFilters(t));
    });
  }
  nodeMatchesFilters(t) {
    if (this.excludedNodeIds.has(t.id))
      return !1;
    for (const [e, n] of Object.entries(this.filters)) {
      if (e === "manuallyHidden") continue;
      const r = t.getData()[e];
      if (!this.matches(r, n)) return !1;
    }
    return !0;
  }
  matches(t, e) {
    if (e === void 0) return !0;
    if (t === void 0) return !1;
    const n = e.value, r = (e == null ? void 0 : e.matchMode) ?? "partial";
    if (typeof n == "string")
      return r === "partial" ? String(t).includes(n) : t === n;
    if (typeof n == "number" || typeof n == "boolean")
      return t === n;
    if (Array.isArray(n))
      return r === "partial" ? n.includes(t) : t === n;
    if (typeof n == "object" && n !== null) {
      const { min: s, max: o } = n;
      return !(typeof t != "number" || s !== void 0 && t < s || o !== void 0 && t > o);
    }
    return !1;
  }
}
class bt {
  /**
   * Initializes a graph inside the specified container using the provided data and options.
   *
   * @param container - The HTMLElement that will serve as the main container for the graph.
   * @param data - The graph data, including nodes and edges, to render.
   * @param options - Optional configuration for the graph's behavior, UI, styling, simulation, etc.
   */
  constructor(t, e, n) {
    f(this, "nodes", /* @__PURE__ */ new Map());
    f(this, "edges", /* @__PURE__ */ new Map());
    /** @private */
    f(this, "UIManager");
    f(this, "notifier");
    f(this, "renderer");
    f(this, "simulation");
    f(this, "queryEngine");
    /** @private */
    f(this, "options");
    f(this, "app_id");
    f(this, "parentGraph");
    f(this, "graphDepth");
    f(this, "listeners");
    var c, l, h;
    if (this.listeners = {
      ready: [],
      nodeAdd: [],
      nodeRemove: [],
      nodeChange: [],
      edgeAdd: [],
      edgeRemove: [],
      edgeChange: [],
      dataBatchChanged: []
    }, this.options = {
      isDirected: !0,
      ...n
    }, ((c = this.options.UI) == null ? void 0 : c.mode) === "static" && (this.options.simulation || (this.options.simulation = {}), this.options.simulation.enabled = !1, this.options.simulation.useWorker = !1, this.options.render || (this.options.render = {}), this.options.render.zoomEnabled = !1, this.options.render.zoomAnimation = !1, this.options.render.dragEnabled = !1, this.options.render.selectionBox || (this.options.render.selectionBox = {}), this.options.render.selectionBox.enabled = !1, this.options.UI.tooltip || (this.options.UI.tooltip = {}), this.options.UI.tooltip.enabled = !1, this.options.UI.contextMenu || (this.options.UI.contextMenu = {}), this.options.UI.contextMenu.enabled = !1), this.graphDepth = 0, this.options.parentGraph) {
      this.setParentGraph(this.options.parentGraph);
      let d = this.parentGraph;
      for (; d; )
        d = d.parentGraph, this.graphDepth++;
    }
    const r = {
      ...this.options.render
    }, s = this.options.UI, o = document.createElement("div");
    this.app_id = Cn(8, "pivotick-app-"), o.id = this.app_id, o.classList.add("pivotick"), t.appendChild(o), this.queryEngine = new kg(this), this.UIManager = new Sg(this, o, s), this.notifier = new _g(this), this.renderer = tu(this, o, r), this.renderer.setupRendering();
    const a = {
      ...this.options.simulation,
      layout: (l = this.options) == null ? void 0 : l.layout
    };
    if (this.simulation = new ee(this, a), e) {
      const d = bt.normalizeGraphData(e);
      this._setData(d == null ? void 0 : d.nodes, d == null ? void 0 : d.edges), (h = this.simulation) == null || h.update(), this.renderer.init(), this.renderer.fitAndCenter(1);
    }
    this.startAndRender();
  }
  on(t, e) {
    this.listeners[t].push(e);
  }
  off(t, e) {
    this.listeners[t] = this.listeners[t].filter((n) => n !== e);
  }
  emit(t, ...e) {
    for (const n of this.listeners[t])
      n(...e);
  }
  async startAndRender() {
    await this.simulation.start(), await this.simulation.waitForSimulationStop(), this.renderer.nextTick(), this.renderer.fitAndCenter(), this.UIManager.callGraphReady(), this.ready();
  }
  /**
   * Normalizes graph data by:
   * 1. Building a hierarchy of nodes (including nested children)
   * 2. Creating synthetic edges for edges that point to collapsed children
   * 3. Hiding edges that connect to invisible child nodes
   *
   * Synthetic edges are placeholder edges created when an edge would point to a
   * node inside a collapsed cluster. Instead of pointing to the invisible child,
   * a synthetic edge is created pointing to the parent cluster node. When the
   * cluster is expanded, synthetic edges are hidden and actual edges are shown.
   *
   * @param data - The raw graph data to normalize
   * @returns Normalized graph data with synthetic edges added
   * @private
   */
  static normalizeGraphData(t) {
    const e = t.nodes.map((l) => bt.normalizeNode(l)), n = /* @__PURE__ */ new Map(), r = (l) => {
      l.children.forEach((h) => {
        n.set(h.id, h), h.hasChildren() && r(h);
      });
    };
    e.forEach((l) => {
      r(l);
    });
    const s = new Map(e.map((l) => [l.id, l])), o = new Map([...s, ...n]), a = t.edges.map((l) => bt.normalizeEdge(l, o)).filter((l) => l !== null), c = [];
    for (const l of a)
      if (!l.from.isChild && l.to.isChild && l.to.parentNode) {
        let h = l.to.parentNode;
        const d = /* @__PURE__ */ new Set();
        for (; h && !d.has(h.id); ) {
          d.add(h.id);
          const u = `synthetic-${l.from.id}-${h.id}`, p = new _t(
            u,
            l.from,
            h,
            // { 'label': `${edge.from.id}-${currentParent.id}` },
            {},
            {},
            null,
            l.to
          );
          if (p.to.isChild && p.hide(), c.push(p), !h.parentNode) break;
          h = h.parentNode;
        }
      }
    return a.push(...c), {
      nodes: e,
      edges: a
    };
  }
  /**
   * Normalizes a node, marking its children and hiding them.
   * @private
   */
  static normalizeNode(t, e = 0) {
    let n = [];
    !(t instanceof Mt) && t.children && (n = t.children.map((s) => bt.normalizeNode(s, e + 1)));
    const r = t instanceof Mt ? t : new Mt(t.id.toString(), t.data, t.style, t.domID, n);
    return r.children.forEach((s) => {
      s.markAsChild(r, e + 1), s.hide();
    }), r.weight = t.weight, r.expanded = t.expanded, r;
  }
  /**
   * Normalizes an edge, hiding it if it connects to a child node in a collapsed cluster.
   * @private
   */
  static normalizeEdge(t, e) {
    var a;
    if (t instanceof _t) return t;
    const n = e, r = n.get(t.from.toString()), s = n.get(t.to.toString());
    if (!r || !s) return null;
    const o = new _t(
      ((a = t.id) == null ? void 0 : a.toString()) ?? `${t.from}-${t.to}`,
      r,
      s,
      t.data,
      t.style
    );
    return (r.isChild || s.isChild) && o.hide(), o;
  }
  ready() {
    this.emit("ready");
  }
  nodeAdd(t) {
    this.emit("nodeAdd", t);
  }
  nodeRemove(t) {
    this.emit("nodeRemove", t);
  }
  nodeChange(t, e, n) {
    this.emit("nodeChange", t, e, n);
  }
  edgeAdd(t) {
    this.emit("edgeAdd", t);
  }
  edgeRemove(t) {
    this.emit("edgeRemove", t);
  }
  edgeChange(t, e, n) {
    this.emit("edgeChange", t, e, n);
  }
  dataBatchChanged(t) {
    t && (this.emit("dataBatchChanged", t), t.forEach((e) => {
      switch (e.type) {
        case "node:add":
          this.nodeAdd(e.node);
          break;
        case "node:change":
          this.nodeChange(e.node, e.previousData, e.nextData);
          break;
        case "node:remove":
          this.nodeRemove(e.node);
          break;
        case "edge:add":
          this.edgeAdd(e.edge);
          break;
        case "edge:change":
          this.edgeChange(e.edge, e.previousData, e.nextData);
          break;
        case "edge:remove":
          this.edgeRemove(e.edge);
          break;
      }
    }));
  }
  /**
   * Returns the current configuration options of the graph.
   */
  getOptions() {
    return this.options;
  }
  /**
   * @private
   * Retrieves the callbacks defined in the options for graph interactions.
   * 
   * @returns A partial `InteractionCallbacks` object, or `undefined` if no callbacks are set.
   */
  getCallbacks() {
    var t;
    return (t = this.options) == null ? void 0 : t.callbacks;
  }
  /**
   * @private
   */
  onChange() {
    var t, e, n;
    (t = this.renderer) == null || t.update(!0), (e = this.simulation) == null || e.update(), (n = this.renderer) == null || n.nextTick();
  }
  /**
   * Updates the graph with new nodes and/or edges.
   * 
   * Existing nodes or edges with matching IDs are replaced; new ones are added.
   * Triggers the `onChange` callback if any updates were applied.
   * 
   * @param newNodes Optional array of nodes to update or add.
   * @param newEdges Optional array of edges to update or add.
   * Triggers `onChange`
   */
  updateData(t, e, n = !0) {
    const r = [];
    t && t.forEach((s) => {
      var o;
      this.nodes.has(s.id) ? (r.push({
        type: "node:change",
        node: s,
        previousData: (o = this.nodes.get(s.id)) == null ? void 0 : o.getData(),
        nextData: s.getData()
      }), this.nodes.set(s.id, s)) : (this.addNode(s), r.push({
        type: "node:add",
        node: s
      }));
    }), e && e.forEach((s) => {
      var o;
      this.edges.has(s.id) ? (r.push({
        type: "edge:change",
        edge: s,
        previousData: (o = this.nodes.get(s.id)) == null ? void 0 : o.getData(),
        nextData: s.getData()
      }), this.edges.set(s.id, s)) : (this.addEdge(s), r.push({
        type: "edge:add",
        edge: s
      }));
    }), (t || e) && this.onChange(), n && this.dataBatchChanged(r);
  }
  /**
   * Replaces all current nodes and edges in the graph with the provided data.
   * Clears existing nodes and edges before setting the new ones.
   * Triggers the `onChange` callback after the update.
   * 
   * @param nodes Array of nodes to set. Defaults to an empty array.
   * @param edges Array of edges to set. Defaults to an empty array.
   */
  setData(t = [], e = []) {
    this.nodes.clear(), this.edges.clear();
    const n = bt.normalizeGraphData({ nodes: t, edges: e });
    this._setData(n == null ? void 0 : n.nodes, n == null ? void 0 : n.edges), this.onChange(), this.startAndRender();
  }
  /** 
   * @private
   */
  _setData(t, e) {
    const n = (s) => {
      s.children.forEach((o) => {
        this.nodes.set(o.id, o), o.hasChildren() && n(o);
      });
    }, r = [];
    t.forEach((s) => {
      this.nodes.set(s.id, s), r.push({
        type: "node:add",
        node: s
      }), n(s);
    }), e.forEach((s) => {
      if (!this.nodes.has(s.from.id) || !this.nodes.has(s.to.id)) {
        console.warn(`Edge is pointing a node that doesn't exist. (${this.nodes.get(s.from.id)}) -> (${this.nodes.get(s.to.id)}). It has been skipped`);
        return;
      }
      this.edges.set(s.id, s), r.push({
        type: "edge:add",
        edge: s
      });
    }), this.dataBatchChanged(r);
  }
  /**
   * Adds a node to the graph.
   * 
   * @throws Error if a node with the same `id` already exists.
   * Triggers `onChange` after the node is successfully added.
   */
  addNode(t) {
    const e = bt.normalizeNode(t);
    if (this.nodes.has(e.id))
      throw new Error(`Node with id ${e.id} already exists.`);
    return this.nodes.set(e.id, e), this.dataBatchChanged([{
      type: "node:add",
      node: e
    }]), this.onChange(), e;
  }
  /**
   * Retrieves a node from the graph by its ID.
   * 
   * Returns a deep clone of the node to prevent external mutations.
   * 
   * @param id The ID of the node or a Node object.
   * @returns A cloned `Node` if found, otherwise `undefined`.
   */
  getNode(t) {
    const e = this._getNode(t);
    return e ? structuredClone(e) : void 0;
  }
  /**
   * Retrieves a node from the graph by its ID.
   * 
   * Returns the actual node instance, allowing direct modifications.
   * 
   * **Warning:** Directly modifying nodes using this method may lead to unexpected behavior.
   * It is generally safer to use `getNode` which returns a cloned instance.
   * 
   * @param id The ID of the node or a Node object.
   * @returns The `Node` if found, otherwise `undefined`.
   */
  getMutableNode(t) {
    return this._getNode(t);
  }
  _getNode(t) {
    if (typeof t == "string") {
      const e = this.nodes.get(t);
      return e || void 0;
    } else return t instanceof Mt ? t : void 0;
  }
  /**
   * Removes a node from the graph by its ID.
   * 
   * Also removes any edges connected to the node.
   * 
   * @param id The ID of the node to remove.
   * Triggers `onChange` after the node and its edges are removed.
   */
  removeNode(t) {
    if (this.nodes.has(t)) {
      this.dataBatchChanged([{
        type: "node:remove",
        node: this.nodes.get(t)
      }]), this.nodes.delete(t);
      for (const [e, n] of this.edges)
        (n.from.id === t || n.to.id === t) && (this.dataBatchChanged([{
          type: "edge:remove",
          edge: this.edges.get(e)
        }]), this.edges.delete(e));
      this.onChange();
    }
  }
  /**
   * Adds an edge to the graph.
   * 
   * Both the source (`from`) and target (`to`) nodes must already exist in the graph.
   * Throws an error if an edge with the same ID already exists.
   * 
   * @param e The edge to add.
   * @throws Error if the edge ID already exists or if either node does not exist.
   * Triggers `onChange` after the edge is successfully added.
   */
  addEdge(t) {
    const e = bt.normalizeEdge(t, this.nodes);
    if (!e)
      throw new Error("Either of the from or to nodes do not exist");
    if (this.edges.has(e.id))
      throw new Error(`Edge with id ${e.id} already exists.`);
    if (!this.nodes.has(e.from.id) || !this.nodes.has(e.to.id))
      throw new Error("Both nodes must exist in the graph before adding an edge.");
    return this.edges.set(e.id, e), this.dataBatchChanged([{
      type: "edge:add",
      edge: e
    }]), this.onChange(), e;
  }
  /**
   * Retrieves an edge from the graph by its ID.
   * 
   * Returns a deep clone of the edge to prevent external mutations.
   * 
   * @param id The ID of the edge.
   * @returns A cloned `Edge` if found, otherwise `undefined`.
   */
  getEdge(t) {
    const e = this.edges.get(t);
    return e ? structuredClone(e) : void 0;
  }
  /**
   * Retrieves an edge from the graph by its ID.
   * 
   * Returns the actual edge instance, allowing direct modifications.
   * 
   * **Warning:** Directly modifying edges using this method may lead to unexpected behavior.
   * It is generally safer to use `getEdge` which returns a cloned instance.
   * 
   * @param id The ID of the edge.
   * @returns The `Edge` if found, otherwise `undefined`.
   */
  getMutableEdge(t) {
    return this.edges.get(t);
  }
  /**
   * Removes an edge from the graph by its ID.
   * 
   * @param id The ID of the edge to remove.
   * Triggers `onChange` after the edge is removed.
   */
  removeEdge(t) {
    this.edges.has(t) && (this.dataBatchChanged([{
      type: "edge:remove",
      edge: this.edges.get(t)
    }]), this.edges.delete(t), this.onChange());
  }
  /**
   * Returns the number of nodes currently in the graph.
   * 
   * @returns The total node count.
   */
  getNodeCount() {
    return this.nodes.size;
  }
  /**
   * Returns the number of edges currently in the graph.
   * 
   * @returns The total edge count.
   */
  getEdgeCount() {
    return this.edges.size;
  }
  /**
   * Retrieves all nodes in the graph.
   * 
   * Returns clones of the nodes to prevent external modifications.
   * 
   * @returns An array of cloned `Node` objects.
   */
  getNodes() {
    return Array.from(this.nodes.values()).filter((t) => !t.isChild).map((t) => t.clone());
  }
  /**
   * Retrieves all nodes in the graph.
   * 
   * Returns the actual node instances, allowing direct modifications.
   * 
   * @remarks
   * ⚠️ **Warning:** Modifying nodes directly may lead to unexpected behavior.
   * It is generally safer to use `getNodes`, which returns cloned instances.
   * 
   * @returns An array of `Node` objects.
   */
  getMutableNodes() {
    return Array.from(this.nodes.values());
  }
  /**
   * Retrieves all visible nodes in the graph. Recursively adding visible children
   * 
   * Returns the actual node instances, allowing direct modifications.
   * 
   * @remarks
   * ⚠️ **Warning:** Modifying nodes directly may lead to unexpected behavior.
   * It is generally safer to use `getNodes`, which returns cloned instances.
   * 
   * @returns An array of `Node` objects.
   */
  getMutableVisibleNodes() {
    return this.getMutableNodes().filter((t) => t.visible);
  }
  /**
   * Retrieves all edges in the graph.
   * 
   * Returns clones of the edges to prevent external modifications.
   * 
   * @returns An array of cloned `Edge` objects.
   */
  getEdges() {
    return Array.from(this.edges.values()).map((t) => t.clone());
  }
  /**
   * Retrieves all edges in the graph.
   * 
   * Returns the actual edge instances, allowing direct modifications.
   * 
   * @remarks
   * ⚠️ **Warning:** Modifying edges directly may lead to unexpected behavior.
   * Use {@link getEdges} instead to work with safe clones.
   * 
   * @returns An array of `Edge` objects.
   */
  getMutableEdges() {
    return Array.from(this.edges.values());
  }
  /**
   * Retrieves all visible edges in the graph.
   * 
   * Returns the actual edge instances, allowing direct modifications.
   * 
   * @remarks
   * ⚠️ **Warning:** Modifying edges directly may lead to unexpected behavior.
   * Use {@link getEdges} instead to work with safe clones.
   * 
   * @returns An array of `Edge` objects.
   */
  getMutableVisibleEdges() {
    return this.getMutableEdges().filter((t) => t.visible);
  }
  /**
   * Finds all edges originating from a given node.
   * 
   * Returns cloned edges to prevent external modifications.
   * 
   * @param node The node or node ID to find outgoing edges from.
   * @returns An array of `Edge` objects whose `from` node matches the query.
   */
  getEdgesFromNode(t) {
    const e = this._getNode(t);
    return e ? this.getEdges().filter((n) => n.from.id === e.id) : [];
  }
  /**
   * Finds all edges pointing to a given node.
   * 
   * Returns cloned edges to prevent external modifications.
   * 
   * @param node The node or node ID to find incoming edges to.
   * @returns An array of `Edge` objects whose `to` node matches the query.
   */
  getEdgesToNode(t) {
    const e = this._getNode(t);
    return e ? this.getEdges().filter((n) => n.to.id === e.id) : [];
  }
  /**
   * Retrieves all nodes directly connected from the given node.
   * 
   * Returns cloned nodes to prevent external modifications.
   * 
   * @param node The node or node ID to find connections from.
   * @returns An array of `Node` objects directly connected from the given node.
   */
  getConnectedNodes(t) {
    const e = this._getNode(t);
    return e ? this.getEdgesFromNode(e.id).map((s) => s.to) : [];
  }
  setVisibleNodes(t) {
    const e = new Set(t.map((r) => r.id));
    let n = !1;
    this.nodes.forEach((r) => {
      const s = e.has(r.id);
      r.visible !== s && (r.toggleVisibility(s), n = !0);
    }), this.edges.forEach((r) => {
      var c, l;
      const s = (((c = r.getSubgraphFromNode()) == null ? void 0 : c.visible) ?? r.from.visible) && (((l = r.getSubgraphToNode()) == null ? void 0 : l.visible) ?? r.to.visible), o = !r.isSynthetic || !r.to.expanded, a = s && o;
      r.visible !== a && (r.toggleVisibility(a), n = !0);
    }), n && this.onChange();
  }
  hideNode(t) {
    t.hide(), t.getEdgesOut().forEach((e) => {
      e.hide();
    }), t.getEdgesIn().forEach((e) => {
      e.hide();
    }), this.onChange();
  }
  showNode(t) {
    t.show(), t.getEdgesOut().forEach((e) => {
      e.target.visible && e.show();
    }), t.getEdgesIn().forEach((e) => {
      e.from.visible && e.show();
    }), this.onChange();
  }
  toggleExpandNode(t) {
    t.toggleExpand(), this.onChange();
  }
  toggleExpandNodes(t) {
    t.forEach((e) => {
      e.toggleExpand();
    }), this.onChange();
  }
  /**
   * Trigger the next render update of the graph.
   */
  nextTick() {
    var t;
    (t = this.renderer) == null || t.nextTick();
  }
  /**
   * Trigger the next render update of the graph for the passed subjects.
   */
  nextTickFor(t) {
    var e;
    (e = this.renderer) == null || e.nextTickFor(t);
  }
  /**
   * Destroy all UI components.
   */
  destroy() {
    this.UIManager.destroy();
  }
  /**
   * The ID of the app
   */
  getAppID() {
    return this.app_id;
  }
  /**
   * @private
   * Set the parent graph instance if this instance is nested as a subgraph
   */
  setParentGraph(t) {
    this.parentGraph = t;
  }
  /**
   * @private
   * Set the parent graph instance if this instance is nested as a subgraph
   */
  getParentGraph() {
    return this.parentGraph;
  }
  getGraphDepth() {
    return this.graphDepth;
  }
  /**
   * @private
   */
  updateLayoutProgress(t, e, n) {
    var r;
    (r = this.renderer) == null || r.updateLayoutProgress(t, e, n);
  }
  /**
   * Brings the specified node or edge into focus within the graph view.
   * 
   * @param element The `Node` or `Edge` to focus.
   */
  focusElement(t) {
    this.renderer.focusElement(t);
  }
  /**
   * Selects a given node or edge in the graph.
   * 
   * @param element The `Node` or `Edge` to select.
   */
  selectElement(t) {
    t instanceof _t ? this.renderer.getGraphInteraction().selectEdge(t.getGraphElement(), t) : t instanceof Mt && this.renderer.getGraphInteraction().selectNode(t.getGraphElement(), t);
  }
  /**
   * Deselect all
   */
  deselectAll() {
    this.renderer.getGraphInteraction().unselectAll();
  }
  /**
   * Add a highligh class to the given node or edge
   * 
   * @param element The `Node` or `Edge` to highligh.
   */
  highlightElement(t) {
    this.renderer.highlightElement(t);
  }
  /**
   * Remove a highligh class to the given node or edge
   * 
   * @param element The `Node` or `Edge` to select.
   */
  unHighlightElement(t) {
    this.renderer.unHighlightElement(t);
  }
}
const sn = {
  pivotick: {
    colors: [
      "#7EA2FB",
      // vibrant-blue
      "#A666F4",
      // vibrant-indigo
      "#85CB33",
      // vibrant-green
      "#FFB74D",
      // amber-orange
      "#4DD0E1",
      // cyan-light
      "#FFD54F",
      // yellowish accent
      "#BA68C8",
      // purple accent
      "#81C784",
      // green-light
      "#00BCD4",
      // cyan-light
      "#FFA726"
      // orange accent
    ],
    maxColors: 10,
    colorblindSafe: !1,
    description: "Official Pivotick palette"
  },
  "d3-category10": {
    colors: [
      "#1f77b4",
      "#ff7f0e",
      "#2ca02c",
      "#d62728",
      "#9467bd",
      "#8c564b",
      "#e377c2",
      "#7f7f7f",
      "#bcbd22",
      "#17becf"
    ],
    maxColors: 10,
    colorblindSafe: !1,
    description: "Classic D3 categorical palette"
  },
  "d3-tableau10": {
    colors: [
      "#4E79A7",
      "#F28E2B",
      "#E15759",
      "#76B7B2",
      "#59A14F",
      "#EDC948",
      "#B07AA1",
      "#FF9DA7",
      "#9C755F",
      "#BAB0AC"
    ],
    maxColors: 10,
    colorblindSafe: !1,
    description: "Modern Tableau 10 palette"
  },
  "okabe-ito": {
    colors: [
      "#E69F00",
      "#56B4E9",
      "#009E73",
      "#F0E442",
      "#0072B2",
      "#D55E00",
      "#CC79A7",
      "#000000"
    ],
    maxColors: 8,
    colorblindSafe: !0,
    description: "Colorblind-safe Okabe-Ito palette"
  },
  "brewer-set3": {
    colors: [
      "#8DD3C7",
      "#FFFFB3",
      "#BEBADA",
      "#FB8072",
      "#80B1D3",
      "#FDB462",
      "#B3DE69",
      "#FCCDE5",
      "#D9D9D9",
      "#BC80BD",
      "#CCEBC5",
      "#FFED6F"
    ],
    maxColors: 12,
    colorblindSafe: !1,
    description: "Large ColorBrewer Set3 palette"
  },
  "tol-bright": {
    colors: [
      "#4477AA",
      "#EE6677",
      "#228833",
      "#CCBB44",
      "#66CCEE",
      "#AA3377",
      "#BBBBBB"
    ],
    maxColors: 7,
    colorblindSafe: !0,
    description: "Paul Tol bright palette"
  },
  "kelly-22": {
    colors: [
      "#F2F3F4",
      "#222222",
      "#F3C300",
      "#875692",
      "#F38400",
      "#A1CAF1",
      "#BE0032",
      "#C2B280",
      "#848482",
      "#008856",
      "#E68FAC",
      "#0067A5",
      "#F99379",
      "#604E97",
      "#F6A600",
      "#B3446C",
      "#DCD300",
      "#882D17",
      "#8DB600",
      "#654522",
      "#E25822",
      "#2B3D26"
    ],
    maxColors: 22,
    colorblindSafe: !1,
    description: "Kelly's 22 colors of maximum contrast"
  },
  "tableau-40": {
    colors: [
      "#4E79A7",
      "#A0CBE8",
      "#F28E2B",
      "#FFBE7D",
      "#59A14F",
      "#8CD17D",
      "#B6992D",
      "#F1CE63",
      "#499894",
      "#86BCB6",
      "#E15759",
      "#FF9D9A",
      "#79706E",
      "#BAB0AC",
      "#D37295",
      "#FABFD2",
      "#B07AA1",
      "#D4A6C8",
      "#9D7660",
      "#D7B5A6"
    ],
    maxColors: 40,
    colorblindSafe: !1,
    description: "Tableau extended palette, 40 colors"
  }
};
class Ng {
  constructor(t) {
    f(this, "palette");
    f(this, "valueToColor", /* @__PURE__ */ new Map());
    f(this, "nextIndex", 0);
    this.palette = this.resolvePalette(t);
  }
  resolvePalette(t) {
    var n;
    if (!t)
      return ((n = sn.pivotick) == null ? void 0 : n.colors) ?? Object.values(sn)[0].colors;
    if (Array.isArray(t)) {
      if (t.length === 0)
        throw new Error("Custom palette array cannot be empty.");
      return t;
    }
    const e = sn[t];
    if (!e)
      throw new Error(`Palette "${t}" not found in PALETTE_REGISTRY.`);
    return e.colors;
  }
  /**
   * Returns a color for the given value.
   * - If the value was already mapped, returns the same color.
   * - If not, assigns the next palette color (cycles if needed).
   */
  getColor(t) {
    if (t == null)
      return this.palette[0];
    const e = this.valueToColor.get(t);
    if (e)
      return e;
    const n = this.palette[this.nextIndex % this.palette.length];
    return this.valueToColor.set(t, n), this.nextIndex++, n;
  }
  /**
   * Clears all mappings and restarts from the beginning of the palette.
   */
  reset() {
    this.valueToColor.clear(), this.nextIndex = 0;
  }
  /**
   * Returns current internal mapping (read-only snapshot).
   */
  getMapping() {
    return new Map(this.valueToColor);
  }
}
bt.Node = Mt;
bt.Edge = _t;
bt.ColorPaletteMapper = Ng;
export {
  Ng as C,
  _t as E,
  bt as G,
  Mt as N,
  ee as S,
  At as T
};
