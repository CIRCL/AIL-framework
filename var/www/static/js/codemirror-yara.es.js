//#region node_modules/@lezer/common/dist/index.js
var e = 0, t = class {
	constructor(e, t) {
		this.from = e, this.to = t;
	}
}, n = class {
	constructor(t = {}) {
		this.id = e++, this.perNode = !!t.perNode, this.deserialize = t.deserialize || (() => {
			throw Error("This node type doesn't define a deserialize function");
		}), this.combine = t.combine || null;
	}
	add(e) {
		if (this.perNode) throw RangeError("Can't add per-node props to node types");
		return typeof e != "function" && (e = a.match(e)), (t) => {
			let n = e(t);
			return n === void 0 ? null : [this, n];
		};
	}
};
n.closedBy = new n({ deserialize: (e) => e.split(" ") }), n.openedBy = new n({ deserialize: (e) => e.split(" ") }), n.group = new n({ deserialize: (e) => e.split(" ") }), n.isolate = new n({ deserialize: (e) => {
	if (e && e != "rtl" && e != "ltr" && e != "auto") throw RangeError("Invalid value for isolate: " + e);
	return e || "auto";
} }), n.contextHash = new n({ perNode: !0 }), n.lookAhead = new n({ perNode: !0 }), n.mounted = new n({ perNode: !0 });
var r = class {
	constructor(e, t, n, r = !1) {
		this.tree = e, this.overlay = t, this.parser = n, this.bracketed = r;
	}
	static get(e) {
		return e && e.props && e.props[n.mounted.id];
	}
}, i = Object.create(null), a = class e {
	constructor(e, t, n, r = 0) {
		this.name = e, this.props = t, this.id = n, this.flags = r;
	}
	static define(t) {
		let n = t.props && t.props.length ? Object.create(null) : i, r = +!!t.top | (t.skipped ? 2 : 0) | (t.error ? 4 : 0) | (t.name == null ? 8 : 0), a = new e(t.name || "", n, t.id, r);
		if (t.props) {
			for (let e of t.props) if (Array.isArray(e) || (e = e(a)), e) {
				if (e[0].perNode) throw RangeError("Can't store a per-node prop on a node type");
				n[e[0].id] = e[1];
			}
		}
		return a;
	}
	prop(e) {
		return this.props[e.id];
	}
	get isTop() {
		return (this.flags & 1) > 0;
	}
	get isSkipped() {
		return (this.flags & 2) > 0;
	}
	get isError() {
		return (this.flags & 4) > 0;
	}
	get isAnonymous() {
		return (this.flags & 8) > 0;
	}
	is(e) {
		if (typeof e == "string") {
			if (this.name == e) return !0;
			let t = this.prop(n.group);
			return t ? t.indexOf(e) > -1 : !1;
		}
		return this.id == e;
	}
	static match(e) {
		let t = Object.create(null);
		for (let n in e) for (let r of n.split(" ")) t[r] = e[n];
		return (e) => {
			for (let r = e.prop(n.group), i = -1; i < (r ? r.length : 0); i++) {
				let n = t[i < 0 ? e.name : r[i]];
				if (n) return n;
			}
		};
	}
};
a.none = new a("", Object.create(null), 0, 8);
var o = class e {
	constructor(e) {
		this.types = e;
		for (let t = 0; t < e.length; t++) if (e[t].id != t) throw RangeError("Node type ids should correspond to array positions when creating a node set");
	}
	extend(...t) {
		let n = [];
		for (let e of this.types) {
			let r = null;
			for (let n of t) {
				let t = n(e);
				if (t) {
					r || (r = Object.assign({}, e.props));
					let n = t[1], i = t[0];
					i.combine && i.id in r && (n = i.combine(r[i.id], n)), r[i.id] = n;
				}
			}
			n.push(r ? new a(e.name, r, e.id, e.flags) : e);
		}
		return new e(n);
	}
}, s = /* @__PURE__ */ new WeakMap(), c = /* @__PURE__ */ new WeakMap(), l;
(function(e) {
	e[e.ExcludeBuffers = 1] = "ExcludeBuffers", e[e.IncludeAnonymous = 2] = "IncludeAnonymous", e[e.IgnoreMounts = 4] = "IgnoreMounts", e[e.IgnoreOverlays = 8] = "IgnoreOverlays", e[e.EnterBracketed = 16] = "EnterBracketed";
})(l || (l = {}));
var u = class e {
	constructor(e, t, n, r, i) {
		if (this.type = e, this.children = t, this.positions = n, this.length = r, this.props = null, i && i.length) {
			this.props = Object.create(null);
			for (let [e, t] of i) this.props[typeof e == "number" ? e : e.id] = t;
		}
	}
	toString() {
		let e = r.get(this);
		if (e && !e.overlay) return e.tree.toString();
		let t = "";
		for (let e of this.children) {
			let n = e.toString();
			n && (t && (t += ","), t += n);
		}
		return this.type.name ? (/\W/.test(this.type.name) && !this.type.isError ? JSON.stringify(this.type.name) : this.type.name) + (t.length ? "(" + t + ")" : "") : t;
	}
	cursor(e = 0) {
		return new te(this.topNode, e);
	}
	cursorAt(e, t = 0, n = 0) {
		let r = new te(s.get(this) || this.topNode);
		return r.moveTo(e, t), s.set(this, r._tree), r;
	}
	get topNode() {
		return new g(this, 0, 0, null);
	}
	resolve(e, t = 0) {
		let n = m(s.get(this) || this.topNode, e, t, !1);
		return s.set(this, n), n;
	}
	resolveInner(e, t = 0) {
		let n = m(c.get(this) || this.topNode, e, t, !0);
		return c.set(this, n), n;
	}
	resolveStack(e, t = 0) {
		return S(this, e, t);
	}
	iterate(e) {
		let { enter: t, leave: n, from: r = 0, to: i = this.length } = e, a = e.mode || 0, o = (a & l.IncludeAnonymous) > 0;
		for (let e = this.cursor(a | l.IncludeAnonymous);;) {
			let a = !1;
			if (e.from <= i && e.to >= r && (!o && e.type.isAnonymous || t(e) !== !1)) {
				if (e.firstChild()) continue;
				a = !0;
			}
			for (; a && n && (o || !e.type.isAnonymous) && n(e), !e.nextSibling();) {
				if (!e.parent()) return;
				a = !0;
			}
		}
	}
	prop(e) {
		return e.perNode ? this.props ? this.props[e.id] : void 0 : this.type.prop(e);
	}
	get propValues() {
		let e = [];
		if (this.props) for (let t in this.props) e.push([+t, this.props[t]]);
		return e;
	}
	balance(t = {}) {
		return this.children.length <= 8 ? this : oe(a.none, this.children, this.positions, 0, this.children.length, 0, this.length, (t, n, r) => new e(this.type, t, n, r, this.propValues), t.makeTree || ((t, n, r) => new e(a.none, t, n, r)));
	}
	static build(e) {
		return re(e);
	}
};
u.empty = new u(a.none, [], [], 0);
var d = class e {
	constructor(e, t) {
		this.buffer = e, this.index = t;
	}
	get id() {
		return this.buffer[this.index - 4];
	}
	get start() {
		return this.buffer[this.index - 3];
	}
	get end() {
		return this.buffer[this.index - 2];
	}
	get size() {
		return this.buffer[this.index - 1];
	}
	get pos() {
		return this.index;
	}
	next() {
		this.index -= 4;
	}
	fork() {
		return new e(this.buffer, this.index);
	}
}, f = class e {
	constructor(e, t, n) {
		this.buffer = e, this.length = t, this.set = n;
	}
	get type() {
		return a.none;
	}
	toString() {
		let e = [];
		for (let t = 0; t < this.buffer.length;) e.push(this.childString(t)), t = this.buffer[t + 3];
		return e.join(",");
	}
	childString(e) {
		let t = this.buffer[e], n = this.buffer[e + 3], r = this.set.types[t], i = r.name;
		if (/\W/.test(i) && !r.isError && (i = JSON.stringify(i)), e += 4, n == e) return i;
		let a = [];
		for (; e < n;) a.push(this.childString(e)), e = this.buffer[e + 3];
		return i + "(" + a.join(",") + ")";
	}
	findChild(e, t, n, r, i) {
		let { buffer: a } = this, o = -1;
		for (let s = e; s != t && !(p(i, r, a[s + 1], a[s + 2]) && (o = s, n > 0)); s = a[s + 3]);
		return o;
	}
	slice(t, n, r) {
		let i = this.buffer, a = new Uint16Array(n - t), o = 0;
		for (let e = t, s = 0; e < n;) {
			a[s++] = i[e++], a[s++] = i[e++] - r;
			let n = a[s++] = i[e++] - r;
			a[s++] = i[e++] - t, o = Math.max(o, n);
		}
		return new e(a, o, this.set);
	}
};
function p(e, t, n, r) {
	switch (e) {
		case -2: return n < t;
		case -1: return r >= t && n < t;
		case 0: return n < t && r > t;
		case 1: return n <= t && r > t;
		case 2: return r > t;
		case 4: return !0;
	}
}
function m(e, t, n, r) {
	for (var i; e.from == e.to || (n < 1 ? e.from >= t : e.from > t) || (n > -1 ? e.to <= t : e.to < t);) {
		let t = !r && e instanceof g && e.index < 0 ? null : e.parent;
		if (!t) return e;
		e = t;
	}
	let a = r ? 0 : l.IgnoreOverlays;
	if (r) for (let r = e, o = r.parent; o; r = o, o = r.parent) r instanceof g && r.index < 0 && ((i = o.enter(t, n, a)) == null ? void 0 : i.from) != r.from && (e = o);
	for (;;) {
		let r = e.enter(t, n, a);
		if (!r) return e;
		e = r;
	}
}
var h = class {
	cursor(e = 0) {
		return new te(this, e);
	}
	getChild(e, t = null, n = null) {
		let r = _(this, e, t, n);
		return r.length ? r[0] : null;
	}
	getChildren(e, t = null, n = null) {
		return _(this, e, t, n);
	}
	resolve(e, t = 0) {
		return m(this, e, t, !1);
	}
	resolveInner(e, t = 0) {
		return m(this, e, t, !0);
	}
	matchContext(e) {
		return v(this.parent, e);
	}
	enterUnfinishedNodesBefore(e) {
		let t = this.childBefore(e), n = this;
		for (; t;) {
			let e = t.lastChild;
			if (!e || e.to != t.to) break;
			e.type.isError && e.from == e.to ? (n = t, t = e.prevSibling) : t = e;
		}
		return n;
	}
	get node() {
		return this;
	}
	get next() {
		return this.parent;
	}
}, g = class e extends h {
	constructor(e, t, n, r) {
		super(), this._tree = e, this.from = t, this.index = n, this._parent = r;
	}
	get type() {
		return this._tree.type;
	}
	get name() {
		return this._tree.type.name;
	}
	get to() {
		return this.from + this._tree.length;
	}
	nextChild(t, n, i, a, o = 0) {
		for (let s = this;;) {
			for (let { children: c, positions: d } = s._tree, m = n > 0 ? c.length : -1; t != m; t += n) {
				let m = c[t], h = d[t] + s.from, g;
				if (!(!(o & l.EnterBracketed && m instanceof u && (g = r.get(m)) && !g.overlay && g.bracketed && i >= h && i <= h + m.length) && !p(a, i, h, h + m.length))) {
					if (m instanceof f) {
						if (o & l.ExcludeBuffers) continue;
						let e = m.findChild(0, m.buffer.length, n, i - h, a);
						if (e > -1) return new b(new y(s, m, t, h), null, e);
					} else if (o & l.IncludeAnonymous || !m.type.isAnonymous || ne(m)) {
						let c;
						if (!(o & l.IgnoreMounts) && (c = r.get(m)) && !c.overlay) return new e(c.tree, h, t, s);
						let u = new e(m, h, t, s);
						return o & l.IncludeAnonymous || !u.type.isAnonymous ? u : u.nextChild(n < 0 ? m.children.length - 1 : 0, n, i, a, o);
					}
				}
			}
			if (o & l.IncludeAnonymous || !s.type.isAnonymous || (t = s.index >= 0 ? s.index + n : n < 0 ? -1 : s._parent._tree.children.length, s = s._parent, !s)) return null;
		}
	}
	get firstChild() {
		return this.nextChild(0, 1, 0, 4);
	}
	get lastChild() {
		return this.nextChild(this._tree.children.length - 1, -1, 0, 4);
	}
	childAfter(e) {
		return this.nextChild(0, 1, e, 2);
	}
	childBefore(e) {
		return this.nextChild(this._tree.children.length - 1, -1, e, -2);
	}
	prop(e) {
		return this._tree.prop(e);
	}
	enter(t, n, i = 0) {
		let a;
		if (!(i & l.IgnoreOverlays) && (a = r.get(this._tree)) && a.overlay) {
			let r = t - this.from, o = i & l.EnterBracketed && a.bracketed;
			for (let { from: t, to: i } of a.overlay) if ((n > 0 || o ? t <= r : t < r) && (n < 0 || o ? i >= r : i > r)) return new e(a.tree, a.overlay[0].from + this.from, -1, this);
		}
		return this.nextChild(0, 1, t, n, i);
	}
	nextSignificantParent() {
		let e = this;
		for (; e.type.isAnonymous && e._parent;) e = e._parent;
		return e;
	}
	get parent() {
		return this._parent ? this._parent.nextSignificantParent() : null;
	}
	get nextSibling() {
		return this._parent && this.index >= 0 ? this._parent.nextChild(this.index + 1, 1, 0, 4) : null;
	}
	get prevSibling() {
		return this._parent && this.index >= 0 ? this._parent.nextChild(this.index - 1, -1, 0, 4) : null;
	}
	get tree() {
		return this._tree;
	}
	toTree() {
		return this._tree;
	}
	toString() {
		return this._tree.toString();
	}
};
function _(e, t, n, r) {
	let i = e.cursor(), a = [];
	if (!i.firstChild()) return a;
	if (n != null) {
		for (let e = !1; !e;) if (e = i.type.is(n), !i.nextSibling()) return a;
	}
	for (;;) {
		if (r != null && i.type.is(r)) return a;
		if (i.type.is(t) && a.push(i.node), !i.nextSibling()) return r == null ? a : [];
	}
}
function v(e, t, n = t.length - 1) {
	for (let r = e; n >= 0; r = r.parent) {
		if (!r) return !1;
		if (!r.type.isAnonymous) {
			if (t[n] && t[n] != r.name) return !1;
			n--;
		}
	}
	return !0;
}
var y = class {
	constructor(e, t, n, r) {
		this.parent = e, this.buffer = t, this.index = n, this.start = r;
	}
}, b = class e extends h {
	get name() {
		return this.type.name;
	}
	get from() {
		return this.context.start + this.context.buffer.buffer[this.index + 1];
	}
	get to() {
		return this.context.start + this.context.buffer.buffer[this.index + 2];
	}
	constructor(e, t, n) {
		super(), this.context = e, this._parent = t, this.index = n, this.type = e.buffer.set.types[e.buffer.buffer[n]];
	}
	child(t, n, r) {
		let { buffer: i } = this.context, a = i.findChild(this.index + 4, i.buffer[this.index + 3], t, n - this.context.start, r);
		return a < 0 ? null : new e(this.context, this, a);
	}
	get firstChild() {
		return this.child(1, 0, 4);
	}
	get lastChild() {
		return this.child(-1, 0, 4);
	}
	childAfter(e) {
		return this.child(1, e, 2);
	}
	childBefore(e) {
		return this.child(-1, e, -2);
	}
	prop(e) {
		return this.type.prop(e);
	}
	enter(t, n, r = 0) {
		if (r & l.ExcludeBuffers) return null;
		let { buffer: i } = this.context, a = i.findChild(this.index + 4, i.buffer[this.index + 3], n > 0 ? 1 : -1, t - this.context.start, n);
		return a < 0 ? null : new e(this.context, this, a);
	}
	get parent() {
		return this._parent || this.context.parent.nextSignificantParent();
	}
	externalSibling(e) {
		return this._parent ? null : this.context.parent.nextChild(this.context.index + e, e, 0, 4);
	}
	get nextSibling() {
		let { buffer: t } = this.context, n = t.buffer[this.index + 3];
		return n < (this._parent ? t.buffer[this._parent.index + 3] : t.buffer.length) ? new e(this.context, this._parent, n) : this.externalSibling(1);
	}
	get prevSibling() {
		let { buffer: t } = this.context, n = this._parent ? this._parent.index + 4 : 0;
		return this.index == n ? this.externalSibling(-1) : new e(this.context, this._parent, t.findChild(n, this.index, -1, 0, 4));
	}
	get tree() {
		return null;
	}
	toTree() {
		let e = [], t = [], { buffer: n } = this.context, r = this.index + 4, i = n.buffer[this.index + 3];
		if (i > r) {
			let a = n.buffer[this.index + 1];
			e.push(n.slice(r, i, a)), t.push(0);
		}
		return new u(this.type, e, t, this.to - this.from);
	}
	toString() {
		return this.context.buffer.childString(this.index);
	}
};
function ee(e) {
	if (!e.length) return null;
	let t = 0, n = e[0];
	for (let r = 1; r < e.length; r++) {
		let i = e[r];
		(i.from > n.from || i.to < n.to) && (n = i, t = r);
	}
	let r = n instanceof g && n.index < 0 ? null : n.parent, i = e.slice();
	return r ? i[t] = r : i.splice(t, 1), new x(i, n);
}
var x = class {
	constructor(e, t) {
		this.heads = e, this.node = t;
	}
	get next() {
		return ee(this.heads);
	}
};
function S(e, t, n) {
	let i = e.resolveInner(t, n), a = null;
	for (let e = i instanceof g ? i : i.context.parent; e; e = e.parent) if (e.index < 0) {
		let r = e.parent;
		(a || (a = [i])).push(r.resolve(t, n)), e = r;
	} else {
		let o = r.get(e.tree);
		if (o && o.overlay && o.overlay[0].from <= t && o.overlay[o.overlay.length - 1].to >= t) {
			let r = new g(o.tree, o.overlay[0].from + e.from, -1, e);
			(a || (a = [i])).push(m(r, t, n, !1));
		}
	}
	return a ? ee(a) : i;
}
var te = class {
	get name() {
		return this.type.name;
	}
	constructor(e, t = 0) {
		if (this.buffer = null, this.stack = [], this.index = 0, this.bufferNode = null, this.mode = t & ~l.EnterBracketed, e instanceof g) this.yieldNode(e);
		else {
			this._tree = e.context.parent, this.buffer = e.context;
			for (let t = e._parent; t; t = t._parent) this.stack.unshift(t.index);
			this.bufferNode = e, this.yieldBuf(e.index);
		}
	}
	yieldNode(e) {
		return e ? (this._tree = e, this.type = e.type, this.from = e.from, this.to = e.to, !0) : !1;
	}
	yieldBuf(e, t) {
		this.index = e;
		let { start: n, buffer: r } = this.buffer;
		return this.type = t || r.set.types[r.buffer[e]], this.from = n + r.buffer[e + 1], this.to = n + r.buffer[e + 2], !0;
	}
	yield(e) {
		return e ? e instanceof g ? (this.buffer = null, this.yieldNode(e)) : (this.buffer = e.context, this.yieldBuf(e.index, e.type)) : !1;
	}
	toString() {
		return this.buffer ? this.buffer.buffer.childString(this.index) : this._tree.toString();
	}
	enterChild(e, t, n) {
		if (!this.buffer) return this.yield(this._tree.nextChild(e < 0 ? this._tree._tree.children.length - 1 : 0, e, t, n, this.mode));
		let { buffer: r } = this.buffer, i = r.findChild(this.index + 4, r.buffer[this.index + 3], e, t - this.buffer.start, n);
		return i < 0 ? !1 : (this.stack.push(this.index), this.yieldBuf(i));
	}
	firstChild() {
		return this.enterChild(1, 0, 4);
	}
	lastChild() {
		return this.enterChild(-1, 0, 4);
	}
	childAfter(e) {
		return this.enterChild(1, e, 2);
	}
	childBefore(e) {
		return this.enterChild(-1, e, -2);
	}
	enter(e, t, n = this.mode) {
		return this.buffer ? n & l.ExcludeBuffers ? !1 : this.enterChild(1, e, t) : this.yield(this._tree.enter(e, t, n));
	}
	parent() {
		if (!this.buffer) return this.yieldNode(this.mode & l.IncludeAnonymous ? this._tree._parent : this._tree.parent);
		if (this.stack.length) return this.yieldBuf(this.stack.pop());
		let e = this.mode & l.IncludeAnonymous ? this.buffer.parent : this.buffer.parent.nextSignificantParent();
		return this.buffer = null, this.yieldNode(e);
	}
	sibling(e) {
		if (!this.buffer) return this._tree._parent ? this.yield(this._tree.index < 0 ? null : this._tree._parent.nextChild(this._tree.index + e, e, 0, 4, this.mode)) : !1;
		let { buffer: t } = this.buffer, n = this.stack.length - 1;
		if (e < 0) {
			let e = n < 0 ? 0 : this.stack[n] + 4;
			if (this.index != e) return this.yieldBuf(t.findChild(e, this.index, -1, 0, 4));
		} else {
			let e = t.buffer[this.index + 3];
			if (e < (n < 0 ? t.buffer.length : t.buffer[this.stack[n] + 3])) return this.yieldBuf(e);
		}
		return n < 0 && this.yield(this.buffer.parent.nextChild(this.buffer.index + e, e, 0, 4, this.mode));
	}
	nextSibling() {
		return this.sibling(1);
	}
	prevSibling() {
		return this.sibling(-1);
	}
	atLastNode(e) {
		let t, n, { buffer: r } = this;
		if (r) {
			if (e > 0) {
				if (this.index < r.buffer.buffer.length) return !1;
			} else for (let e = 0; e < this.index; e++) if (r.buffer.buffer[e + 3] < this.index) return !1;
			({index: t, parent: n} = r);
		} else ({index: t, _parent: n} = this._tree);
		for (; n; {index: t, _parent: n} = n) if (t > -1) for (let r = t + e, i = e < 0 ? -1 : n._tree.children.length; r != i; r += e) {
			let e = n._tree.children[r];
			if (this.mode & l.IncludeAnonymous || e instanceof f || !e.type.isAnonymous || ne(e)) return !1;
		}
		return !0;
	}
	move(e, t) {
		if (t && this.enterChild(e, 0, 4)) return !0;
		for (;;) {
			if (this.sibling(e)) return !0;
			if (this.atLastNode(e) || !this.parent()) return !1;
		}
	}
	next(e = !0) {
		return this.move(1, e);
	}
	prev(e = !0) {
		return this.move(-1, e);
	}
	moveTo(e, t = 0) {
		for (; (this.from == this.to || (t < 1 ? this.from >= e : this.from > e) || (t > -1 ? this.to <= e : this.to < e)) && this.parent(););
		for (; this.enterChild(1, e, t););
		return this;
	}
	get node() {
		if (!this.buffer) return this._tree;
		let e = this.bufferNode, t = null, n = 0;
		if (e && e.context == this.buffer) scan: for (let r = this.index, i = this.stack.length; i >= 0;) {
			for (let a = e; a; a = a._parent) if (a.index == r) {
				if (r == this.index) return a;
				t = a, n = i + 1;
				break scan;
			}
			r = this.stack[--i];
		}
		for (let e = n; e < this.stack.length; e++) t = new b(this.buffer, t, this.stack[e]);
		return this.bufferNode = new b(this.buffer, t, this.index);
	}
	get tree() {
		return this.buffer ? null : this._tree._tree;
	}
	iterate(e, t) {
		for (let n = 0;;) {
			let r = !1;
			if (this.type.isAnonymous || e(this) !== !1) {
				if (this.firstChild()) {
					n++;
					continue;
				}
				this.type.isAnonymous || (r = !0);
			}
			for (;;) {
				if (r && t && t(this), r = this.type.isAnonymous, !n) return;
				if (this.nextSibling()) break;
				this.parent(), n--, r = !0;
			}
		}
	}
	matchContext(e) {
		if (!this.buffer) return v(this.node.parent, e);
		let { buffer: t } = this.buffer, { types: n } = t.set;
		for (let r = e.length - 1, i = this.stack.length - 1; r >= 0; i--) {
			if (i < 0) return v(this._tree, e, r);
			let a = n[t.buffer[this.stack[i]]];
			if (!a.isAnonymous) {
				if (e[r] && e[r] != a.name) return !1;
				r--;
			}
		}
		return !0;
	}
};
function ne(e) {
	return e.children.some((e) => e instanceof f || !e.type.isAnonymous || ne(e));
}
function re(e) {
	var t;
	let { buffer: r, nodeSet: i, maxBufferLength: a = 1024, reused: o = [], minRepeatType: s = i.types.length } = e, c = Array.isArray(r) ? new d(r, r.length) : r, l = i.types, p = 0, m = 0;
	function h(e, t, n, r, u, d) {
		let { id: x, start: S, end: te, size: ne } = c, re = m, ie = p;
		if (ne < 0) {
			if (c.next(), ne == -1) {
				let t = o[x];
				n.push(t), r.push(S - e);
				return;
			}
			if (ne == -3) {
				p = x;
				return;
			}
			if (ne == -4) {
				m = x;
				return;
			}
			throw RangeError(`Unrecognized record size: ${ne}`);
		}
		let ae = l[x], se, ce, le = S - e;
		if (te - S <= a && (ce = b(c.pos - t, u))) {
			let t = new Uint16Array(ce.size - ce.skip), n = c.pos - ce.size, r = t.length;
			for (; c.pos > n;) r = ee(ce.start, t, r);
			se = new f(t, te - ce.start, i), le = ce.start - e;
		} else {
			let e = c.pos - ne;
			c.next();
			let t = [], n = [], r = x >= s ? x : -1, i = 0, o = te;
			for (; c.pos > e;) r >= 0 && c.id == r && c.size >= 0 ? (c.end <= o - a && (v(t, n, S, i, c.end, o, r, re, ie), i = t.length, o = c.end), c.next()) : d > 2500 ? g(S, e, t, n) : h(S, e, t, n, r, d + 1);
			if (r >= 0 && i > 0 && i < t.length && v(t, n, S, i, S, o, r, re, ie), t.reverse(), n.reverse(), r > -1 && i > 0) {
				let e = _(ae, ie);
				se = oe(ae, t, n, 0, t.length, 0, te - S, e, e);
			} else se = y(ae, t, n, te - S, re - te, ie);
		}
		n.push(se), r.push(le);
	}
	function g(e, t, n, r) {
		let o = [], s = 0, l = -1;
		for (; c.pos > t;) {
			let { id: e, start: t, end: n, size: r } = c;
			if (r > 4) c.next();
			else if (l > -1 && t < l) break;
			else l < 0 && (l = n - a), o.push(e, t, n), s++, c.next();
		}
		if (s) {
			let t = new Uint16Array(s * 4), a = o[o.length - 2];
			for (let e = o.length - 3, n = 0; e >= 0; e -= 3) t[n++] = o[e], t[n++] = o[e + 1] - a, t[n++] = o[e + 2] - a, t[n++] = n;
			n.push(new f(t, o[2] - a, i)), r.push(a - e);
		}
	}
	function _(e, t) {
		return (r, i, a) => {
			let o = 0, s = r.length - 1, c, l;
			if (s >= 0 && (c = r[s]) instanceof u) {
				if (!s && c.type == e && c.length == a) return c;
				(l = c.prop(n.lookAhead)) && (o = i[s] + c.length + l);
			}
			return y(e, r, i, a, o, t);
		};
	}
	function v(e, t, n, r, a, o, s, c, l) {
		let u = [], d = [];
		for (; e.length > r;) u.push(e.pop()), d.push(t.pop() + n - a);
		e.push(y(i.types[s], u, d, o - a, c - o, l)), t.push(a - n);
	}
	function y(e, t, r, i, a, o, s) {
		if (o) {
			let e = [n.contextHash, o];
			s = s ? [e].concat(s) : [e];
		}
		if (a > 25) {
			let e = [n.lookAhead, a];
			s = s ? [e].concat(s) : [e];
		}
		return new u(e, t, r, i, s);
	}
	function b(e, t) {
		let n = c.fork(), r = 0, i = 0, o = 0, l = n.end - a, u = {
			size: 0,
			start: 0,
			skip: 0
		};
		scan: for (let a = n.pos - e; n.pos > a;) {
			let e = n.size;
			if (n.id == t && e >= 0) {
				u.size = r, u.start = i, u.skip = o, o += 4, r += 4, n.next();
				continue;
			}
			let c = n.pos - e;
			if (e < 0 || c < a || n.start < l) break;
			let d = n.id >= s ? 4 : 0, f = n.start;
			for (n.next(); n.pos > c;) {
				if (n.size < 0) {
					if (n.size == -3 || n.size == -4) d += 4;
					else break scan;
				} else n.id >= s && (d += 4);
				n.next();
			}
			i = f, r += e, o += d;
		}
		return (t < 0 || r == e) && (u.size = r, u.start = i, u.skip = o), u.size > 4 ? u : void 0;
	}
	function ee(e, t, n) {
		let { id: r, start: i, end: a, size: o } = c;
		if (c.next(), o >= 0 && r < s) {
			let s = n;
			if (o > 4) {
				let r = c.pos - (o - 4);
				for (; c.pos > r;) n = ee(e, t, n);
			}
			t[--n] = s, t[--n] = a - e, t[--n] = i - e, t[--n] = r;
		} else o == -3 ? p = r : o == -4 && (m = r);
		return n;
	}
	let x = [], S = [];
	for (; c.pos > 0;) h(e.start || 0, e.bufferStart || 0, x, S, -1, 0);
	let te = (t = e.length) == null ? x.length ? S[0] + x[0].length : 0 : t;
	return new u(l[e.topID], x.reverse(), S.reverse(), te);
}
var ie = /* @__PURE__ */ new WeakMap();
function ae(e, t) {
	if (!e.isAnonymous || t instanceof f || t.type != e) return 1;
	let n = ie.get(t);
	if (n == null) {
		n = 1;
		for (let r of t.children) {
			if (r.type != e || !(r instanceof u)) {
				n = 1;
				break;
			}
			n += ae(e, r);
		}
		ie.set(t, n);
	}
	return n;
}
function oe(e, t, n, r, i, a, o, s, c) {
	let l = 0;
	for (let n = r; n < i; n++) l += ae(e, t[n]);
	let u = Math.ceil(l * 1.5 / 8), d = [], f = [];
	function p(t, n, r, i, o) {
		for (let s = r; s < i;) {
			let r = s, l = n[s], m = ae(e, t[s]);
			for (s++; s < i; s++) {
				let n = ae(e, t[s]);
				if (m + n >= u) break;
				m += n;
			}
			if (s == r + 1) {
				if (m > u) {
					let e = t[r];
					p(e.children, e.positions, 0, e.children.length, n[r] + o);
					continue;
				}
				d.push(t[r]);
			} else {
				let i = n[s - 1] + t[s - 1].length - l;
				d.push(oe(e, t, n, r, s, l, i, null, c));
			}
			f.push(l + o - a);
		}
	}
	return p(t, n, r, i, 0), (s || c)(d, f, o);
}
var se = class e {
	constructor(e, t, n, r, i = !1, a = !1) {
		this.from = e, this.to = t, this.tree = n, this.offset = r, this.open = !!i | (a ? 2 : 0);
	}
	get openStart() {
		return (this.open & 1) > 0;
	}
	get openEnd() {
		return (this.open & 2) > 0;
	}
	static addTree(t, n = [], r = !1) {
		let i = [new e(0, t.length, t, 0, !1, r)];
		for (let e of n) e.to > t.length && i.push(e);
		return i;
	}
	static applyChanges(t, n, r = 128) {
		if (!n.length) return t;
		let i = [], a = 1, o = t.length ? t[0] : null;
		for (let s = 0, c = 0, l = 0;; s++) {
			let u = s < n.length ? n[s] : null, d = u ? u.fromA : 1e9;
			if (d - c >= r) for (; o && o.from < d;) {
				let n = o;
				if (c >= n.from || d <= n.to || l) {
					let t = Math.max(n.from, c) - l, r = Math.min(n.to, d) - l;
					n = t >= r ? null : new e(t, r, n.tree, n.offset + l, s > 0, !!u);
				}
				if (n && i.push(n), o.to > d) break;
				o = a < t.length ? t[a++] : null;
			}
			if (!u) break;
			c = u.toA, l = u.toA - u.toB;
		}
		return i;
	}
}, ce = class {
	startParse(e, n, r) {
		return typeof e == "string" && (e = new le(e)), r = r ? r.length ? r.map((e) => new t(e.from, e.to)) : [new t(0, 0)] : [new t(0, e.length)], this.createParse(e, n || [], r);
	}
	parse(e, t, n) {
		let r = this.startParse(e, t, n);
		for (;;) {
			let e = r.advance();
			if (e) return e;
		}
	}
}, le = class {
	constructor(e) {
		this.string = e;
	}
	get length() {
		return this.string.length;
	}
	chunk(e) {
		return this.string.slice(e);
	}
	get lineChunks() {
		return !1;
	}
	read(e, t) {
		return this.string.slice(e, t);
	}
};
new n({ perNode: !0 });
//#endregion
//#region node_modules/@marijn/find-cluster-break/src/index.js
var ue = [], de = [];
(() => {
	let e = "lc,34,7n,7,7b,19,,,,2,,2,,,20,b,1c,l,g,,2t,7,2,6,2,2,,4,z,,u,r,2j,b,1m,9,9,,o,4,,9,,3,,5,17,3,1n,9,16,o,,x,1i,3,,i,,7,a,2,t,3,1k,,,7,2,2,2,3,9,,a,2,q,,2,3,1k,,,5,4,2,2,3,3,,u,2,3,,b,3,1k,,,8,,3,,3,k,2,m,6,,3,1k,,,7,2,2,2,3,7,3,a,2,u,,1n,5,3,3,,4,9,,14,5,1j,,,7,,3,,4,7,2,b,2,t,3,1k,,,7,,3,,4,7,2,b,2,f,,c,4,1j,2,,7,,3,,4,9,,a,2,t,3,1y,,4,6,,,,8,i,2,1p,,,8,c,8,2q,,,a,b,7,21,2,r,,,,,,4,2,1d,k,,2,5,b,,10,9,,2u,b,,6,n,4,4,3,g,4,d,,,3,6,,f,,jj,3,qa,4,s,3,t,2,u,2,1s,w,9,,19,3,,,39,2,y,,3a,c,4,c,63,5,1l,a,,,,,2,o,2,,1c,1a,2,c,k,5,1b,h,12,9,c,3,u,d,1k,e,1c,k,48,3,,l,4,,6,,2,3,5i,1s,ek,,5f,x,2da,3,3x,,2o,w,fe,6,2x,2,n9w,4,,a,w,2,28,2,7k,,3,,4,,n,5,4,,2b,2,1e,i,q,i,d,,12,8,p,d,18,4,1b,e,10,,1v,e,c,,8,2,1a,,1f,,,3,2,2,5,2,,,15,5,5,2,6k,8,,2,fn4,,kh,g,g,g,a6,2,gt,,6a,,45,5,1ae,3,,2,5,4,14,3,4,,4l,2,fx,4,1t,5,8t,2,25,6,1y,b,1d,4,3e,3,1h,f,15,,2,2,a,4,19,b,7,,1p,3,10,e,g,2,18,,c,3,1c,e,8,4,,2,2k,c,6,,2,,4d,c,l,4,1j,2,,7,2,2,2,3,9,,a,2,2,7,3,5,1v,9,,,2,,,4,,5,,,e,2,2a,i,n,,29,k,6j,7,2,9,r,2,2a,h,2y,d,2t,3,2,a,74,f,6t,6,,2,2,4,,,,2,3x,7,2,7,3,,s,a,14,7,,4,8,,9,b,1a,g,5i,8,5j,8,,8,2a,m,,e,3e,6,3,,,2,,7,,,1u,5,,2,,5,9n,4,9,2,,,1c,7,3,5,n,,44l,,6,f,8ug,i,1xc,5,1n,7,t4,,,1j,7,4,29,,b,2,f57,2,3mp,1a,2,n,f2,5,3,6,8,8,2,7,u,4,44,3,1iz,1j,4,1e,8,,e,,m,5,,f,11s,7,,h,2,7,,2,,5,2s,,4g,7,af,,1p,4,e4,4,72,2,6r,,2,,7,2,5,,d6,7,31,7,240,5".split(",").map((e) => e ? parseInt(e, 36) : 1);
	for (let t = 0, n = 0; t < e.length; t++) (t % 2 ? de : ue).push(n += e[t]);
})();
function fe(e) {
	if (e < 768) return !1;
	for (let t = 0, n = ue.length;;) {
		let r = t + n >> 1;
		if (e < ue[r]) n = r;
		else if (e >= de[r]) t = r + 1;
		else return !0;
		if (t == n) return !1;
	}
}
function pe(e) {
	return e >= 127462 && e <= 127487;
}
var me = 8205;
function he(e, t, n = !0, r = !0) {
	return (n ? ge : _e)(e, t, r);
}
function ge(e, t, n) {
	if (t == e.length) return t;
	t && ye(e.charCodeAt(t)) && be(e.charCodeAt(t - 1)) && t--;
	let r = ve(e, t);
	for (t += xe(r); t < e.length;) {
		let i = ve(e, t);
		if (r == me || i == me || n && fe(i)) t += xe(i), r = i;
		else if (pe(i)) {
			let n = 0, r = t - 2;
			for (; r >= 0 && pe(ve(e, r));) n++, r -= 2;
			if (n % 2 == 0) break;
			t += 2;
		} else break;
	}
	return t;
}
function _e(e, t, n) {
	for (; t > 1;) {
		let r = ge(e, t - 2, n);
		if (r < t) return r;
		t--;
	}
	return 0;
}
function ve(e, t) {
	let n = e.charCodeAt(t);
	if (!be(n) || t + 1 == e.length) return n;
	let r = e.charCodeAt(t + 1);
	return ye(r) ? (n - 55296 << 10) + (r - 56320) + 65536 : n;
}
function ye(e) {
	return e >= 56320 && e < 57344;
}
function be(e) {
	return e >= 55296 && e < 56320;
}
function xe(e) {
	return e < 65536 ? 1 : 2;
}
//#endregion
//#region node_modules/@codemirror/state/dist/index.js
var C = class e {
	lineAt(e) {
		if (e < 0 || e > this.length) throw RangeError(`Invalid position ${e} in document of length ${this.length}`);
		return this.lineInner(e, !1, 1, 0);
	}
	line(e) {
		if (e < 1 || e > this.lines) throw RangeError(`Invalid line number ${e} in ${this.lines}-line document`);
		return this.lineInner(e, !0, 1, 0);
	}
	replace(e, t, n) {
		[e, t] = je(this, e, t);
		let r = [];
		return this.decompose(0, e, r, 2), n.length && n.decompose(0, n.length, r, 3), this.decompose(t, this.length, r, 1), Ce.from(r, this.length - (t - e) + n.length);
	}
	append(e) {
		return this.replace(this.length, this.length, e);
	}
	slice(e, t = this.length) {
		[e, t] = je(this, e, t);
		let n = [];
		return this.decompose(e, t, n, 0), Ce.from(n, t - e);
	}
	eq(e) {
		if (e == this) return !0;
		if (e.length != this.length || e.lines != this.lines) return !1;
		let t = this.scanIdentical(e, 1), n = this.length - this.scanIdentical(e, -1), r = new De(this), i = new De(e);
		for (let e = t, a = t;;) {
			if (r.next(e), i.next(e), e = 0, r.lineBreak != i.lineBreak || r.done != i.done || r.value != i.value) return !1;
			if (a += r.value.length, r.done || a >= n) return !0;
		}
	}
	iter(e = 1) {
		return new De(this, e);
	}
	iterRange(e, t = this.length) {
		return new Oe(this, e, t);
	}
	iterLines(e, t) {
		let n;
		if (e == null) n = this.iter();
		else {
			t == null && (t = this.lines + 1);
			let r = this.line(e).from;
			n = this.iterRange(r, Math.max(r, t == this.lines + 1 ? this.length : t <= 1 ? 0 : this.line(t - 1).to));
		}
		return new ke(n);
	}
	toString() {
		return this.sliceString(0);
	}
	toJSON() {
		let e = [];
		return this.flatten(e), e;
	}
	constructor() {}
	static of(t) {
		if (t.length == 0) throw RangeError("A document must have at least one line");
		return t.length == 1 && !t[0] ? e.empty : t.length <= 32 ? new Se(t) : Ce.from(Se.split(t, []));
	}
}, Se = class e extends C {
	constructor(e, t = we(e)) {
		super(), this.text = e, this.length = t;
	}
	get lines() {
		return this.text.length;
	}
	get children() {
		return null;
	}
	lineInner(e, t, n, r) {
		for (let i = 0;; i++) {
			let a = this.text[i], o = r + a.length;
			if ((t ? n : o) >= e) return new Ae(r, o, n, a);
			r = o + 1, n++;
		}
	}
	decompose(t, n, r, i) {
		let a = t <= 0 && n >= this.length ? this : new e(Ee(this.text, t, n), Math.min(n, this.length) - Math.max(0, t));
		if (i & 1) {
			let t = r.pop(), n = Te(a.text, t.text.slice(), 0, a.length);
			if (n.length <= 32) r.push(new e(n, t.length + a.length));
			else {
				let t = n.length >> 1;
				r.push(new e(n.slice(0, t)), new e(n.slice(t)));
			}
		} else r.push(a);
	}
	replace(t, n, r) {
		if (!(r instanceof e)) return super.replace(t, n, r);
		[t, n] = je(this, t, n);
		let i = Te(this.text, Te(r.text, Ee(this.text, 0, t)), n), a = this.length + r.length - (n - t);
		return i.length <= 32 ? new e(i, a) : Ce.from(e.split(i, []), a);
	}
	sliceString(e, t = this.length, n = "\n") {
		[e, t] = je(this, e, t);
		let r = "";
		for (let i = 0, a = 0; i <= t && a < this.text.length; a++) {
			let o = this.text[a], s = i + o.length;
			i > e && a && (r += n), e < s && t > i && (r += o.slice(Math.max(0, e - i), t - i)), i = s + 1;
		}
		return r;
	}
	flatten(e) {
		for (let t of this.text) e.push(t);
	}
	scanIdentical() {
		return 0;
	}
	static split(t, n) {
		let r = [], i = -1;
		for (let a of t) r.push(a), i += a.length + 1, r.length == 32 && (n.push(new e(r, i)), r = [], i = -1);
		return i > -1 && n.push(new e(r, i)), n;
	}
}, Ce = class e extends C {
	constructor(e, t) {
		super(), this.children = e, this.length = t, this.lines = 0;
		for (let t of e) this.lines += t.lines;
	}
	lineInner(e, t, n, r) {
		for (let i = 0;; i++) {
			let a = this.children[i], o = r + a.length, s = n + a.lines - 1;
			if ((t ? s : o) >= e) return a.lineInner(e, t, n, r);
			r = o + 1, n = s + 1;
		}
	}
	decompose(e, t, n, r) {
		for (let i = 0, a = 0; a <= t && i < this.children.length; i++) {
			let o = this.children[i], s = a + o.length;
			if (e <= s && t >= a) {
				let i = r & (a <= e | (s >= t ? 2 : 0));
				a >= e && s <= t && !i ? n.push(o) : o.decompose(e - a, t - a, n, i);
			}
			a = s + 1;
		}
	}
	replace(t, n, r) {
		if ([t, n] = je(this, t, n), r.lines < this.lines) for (let i = 0, a = 0; i < this.children.length; i++) {
			let o = this.children[i], s = a + o.length;
			if (t >= a && n <= s) {
				let c = o.replace(t - a, n - a, r), l = this.lines - o.lines + c.lines;
				if (c.lines < l >> 4 && c.lines > l >> 6) {
					let a = this.children.slice();
					return a[i] = c, new e(a, this.length - (n - t) + r.length);
				}
				return super.replace(a, s, c);
			}
			a = s + 1;
		}
		return super.replace(t, n, r);
	}
	sliceString(e, t = this.length, n = "\n") {
		[e, t] = je(this, e, t);
		let r = "";
		for (let i = 0, a = 0; i < this.children.length && a <= t; i++) {
			let o = this.children[i], s = a + o.length;
			a > e && i && (r += n), e < s && t > a && (r += o.sliceString(e - a, t - a, n)), a = s + 1;
		}
		return r;
	}
	flatten(e) {
		for (let t of this.children) t.flatten(e);
	}
	scanIdentical(t, n) {
		if (!(t instanceof e)) return 0;
		let r = 0, [i, a, o, s] = n > 0 ? [
			0,
			0,
			this.children.length,
			t.children.length
		] : [
			this.children.length - 1,
			t.children.length - 1,
			-1,
			-1
		];
		for (;; i += n, a += n) {
			if (i == o || a == s) return r;
			let e = this.children[i], c = t.children[a];
			if (e != c) return r + e.scanIdentical(c, n);
			r += e.length + 1;
		}
	}
	static from(t, n = t.reduce((e, t) => e + t.length + 1, -1)) {
		let r = 0;
		for (let e of t) r += e.lines;
		if (r < 32) {
			let e = [];
			for (let n of t) n.flatten(e);
			return new Se(e, n);
		}
		let i = Math.max(32, r >> 5), a = i << 1, o = i >> 1, s = [], c = 0, l = -1, u = [];
		function d(t) {
			let n;
			if (t.lines > a && t instanceof e) for (let e of t.children) d(e);
			else t.lines > o && (c > o || !c) ? (f(), s.push(t)) : t instanceof Se && c && (n = u[u.length - 1]) instanceof Se && t.lines + n.lines <= 32 ? (c += t.lines, l += t.length + 1, u[u.length - 1] = new Se(n.text.concat(t.text), n.length + 1 + t.length)) : (c + t.lines > i && f(), c += t.lines, l += t.length + 1, u.push(t));
		}
		function f() {
			c != 0 && (s.push(u.length == 1 ? u[0] : e.from(u, l)), l = -1, c = u.length = 0);
		}
		for (let e of t) d(e);
		return f(), s.length == 1 ? s[0] : new e(s, n);
	}
};
C.empty = /*@__PURE__*/ new Se([""], 0);
function we(e) {
	let t = -1;
	for (let n of e) t += n.length + 1;
	return t;
}
function Te(e, t, n = 0, r = 1e9) {
	for (let i = 0, a = 0, o = !0; a < e.length && i <= r; a++) {
		let s = e[a], c = i + s.length;
		c >= n && (c > r && (s = s.slice(0, r - i)), i < n && (s = s.slice(n - i)), o ? (t[t.length - 1] += s, o = !1) : t.push(s)), i = c + 1;
	}
	return t;
}
function Ee(e, t, n) {
	return Te(e, [""], t, n);
}
var De = class {
	constructor(e, t = 1) {
		this.dir = t, this.done = !1, this.lineBreak = !1, this.value = "", this.nodes = [e], this.offsets = [t > 0 ? 1 : (e instanceof Se ? e.text.length : e.children.length) << 1];
	}
	nextInner(e, t) {
		for (this.done = this.lineBreak = !1;;) {
			let n = this.nodes.length - 1, r = this.nodes[n], i = this.offsets[n], a = i >> 1, o = r instanceof Se ? r.text.length : r.children.length;
			if (a == (t > 0 ? o : 0)) {
				if (n == 0) return this.done = !0, this.value = "", this;
				t > 0 && this.offsets[n - 1]++, this.nodes.pop(), this.offsets.pop();
			} else if ((i & 1) == (t > 0 ? 0 : 1)) {
				if (this.offsets[n] += t, e == 0) return this.lineBreak = !0, this.value = "\n", this;
				e--;
			} else if (r instanceof Se) {
				let i = r.text[a + (t < 0 ? -1 : 0)];
				if (this.offsets[n] += t, i.length > Math.max(0, e)) return this.value = e == 0 ? i : t > 0 ? i.slice(e) : i.slice(0, i.length - e), this;
				e -= i.length;
			} else {
				let i = r.children[a + (t < 0 ? -1 : 0)];
				e > i.length ? (e -= i.length, this.offsets[n] += t) : (t < 0 && this.offsets[n]--, this.nodes.push(i), this.offsets.push(t > 0 ? 1 : (i instanceof Se ? i.text.length : i.children.length) << 1));
			}
		}
	}
	next(e = 0) {
		return e < 0 && (this.nextInner(-e, -this.dir), e = this.value.length), this.nextInner(e, this.dir);
	}
}, Oe = class {
	constructor(e, t, n) {
		this.value = "", this.done = !1, this.cursor = new De(e, t > n ? -1 : 1), this.pos = t > n ? e.length : 0, this.from = Math.min(t, n), this.to = Math.max(t, n);
	}
	nextInner(e, t) {
		if (t < 0 ? this.pos <= this.from : this.pos >= this.to) return this.value = "", this.done = !0, this;
		e += Math.max(0, t < 0 ? this.pos - this.to : this.from - this.pos);
		let n = t < 0 ? this.pos - this.from : this.to - this.pos;
		e > n && (e = n), n -= e;
		let { value: r } = this.cursor.next(e);
		return this.pos += (r.length + e) * t, this.value = r.length <= n ? r : t < 0 ? r.slice(r.length - n) : r.slice(0, n), this.done = !this.value, this;
	}
	next(e = 0) {
		return e < 0 ? e = Math.max(e, this.from - this.pos) : e > 0 && (e = Math.min(e, this.to - this.pos)), this.nextInner(e, this.cursor.dir);
	}
	get lineBreak() {
		return this.cursor.lineBreak && this.value != "";
	}
}, ke = class {
	constructor(e) {
		this.inner = e, this.afterBreak = !0, this.value = "", this.done = !1;
	}
	next(e = 0) {
		let { done: t, lineBreak: n, value: r } = this.inner.next(e);
		return t && this.afterBreak ? (this.value = "", this.afterBreak = !1) : t ? (this.done = !0, this.value = "") : n ? this.afterBreak ? this.value = "" : (this.afterBreak = !0, this.next()) : (this.value = r, this.afterBreak = !1), this;
	}
	get lineBreak() {
		return !1;
	}
};
typeof Symbol < "u" && (C.prototype[Symbol.iterator] = function() {
	return this.iter();
}, De.prototype[Symbol.iterator] = Oe.prototype[Symbol.iterator] = ke.prototype[Symbol.iterator] = function() {
	return this;
});
var Ae = class {
	constructor(e, t, n, r) {
		this.from = e, this.to = t, this.number = n, this.text = r;
	}
	get length() {
		return this.to - this.from;
	}
};
function je(e, t, n) {
	return t = Math.max(0, Math.min(e.length, t)), [t, Math.max(t, Math.min(e.length, n))];
}
function w(e, t, n = !0, r = !0) {
	return he(e, t, n, r);
}
function Me(e) {
	return e >= 56320 && e < 57344;
}
function Ne(e) {
	return e >= 55296 && e < 56320;
}
function Pe(e, t) {
	let n = e.charCodeAt(t);
	if (!Ne(n) || t + 1 == e.length) return n;
	let r = e.charCodeAt(t + 1);
	return Me(r) ? (n - 55296 << 10) + (r - 56320) + 65536 : n;
}
function Fe(e) {
	return e <= 65535 ? String.fromCharCode(e) : (e -= 65536, String.fromCharCode((e >> 10) + 55296, (e & 1023) + 56320));
}
function Ie(e) {
	return e < 65536 ? 1 : 2;
}
var Le = /\r\n?|\n/, T = /*@__PURE__*/ (function(e) {
	return e[e.Simple = 0] = "Simple", e[e.TrackDel = 1] = "TrackDel", e[e.TrackBefore = 2] = "TrackBefore", e[e.TrackAfter = 3] = "TrackAfter", e;
})(T || (T = {})), Re = class e {
	constructor(e) {
		this.sections = e;
	}
	get length() {
		let e = 0;
		for (let t = 0; t < this.sections.length; t += 2) e += this.sections[t];
		return e;
	}
	get newLength() {
		let e = 0;
		for (let t = 0; t < this.sections.length; t += 2) {
			let n = this.sections[t + 1];
			e += n < 0 ? this.sections[t] : n;
		}
		return e;
	}
	get empty() {
		return this.sections.length == 0 || this.sections.length == 2 && this.sections[1] < 0;
	}
	iterGaps(e) {
		for (let t = 0, n = 0, r = 0; t < this.sections.length;) {
			let i = this.sections[t++], a = this.sections[t++];
			a < 0 ? (e(n, r, i), r += i) : r += a, n += i;
		}
	}
	iterChangedRanges(e, t = !1) {
		Ve(this, e, t);
	}
	get invertedDesc() {
		let t = [];
		for (let e = 0; e < this.sections.length;) {
			let n = this.sections[e++], r = this.sections[e++];
			r < 0 ? t.push(n, r) : t.push(r, n);
		}
		return new e(t);
	}
	composeDesc(e) {
		return this.empty ? e : e.empty ? this : Ue(this, e);
	}
	mapDesc(e, t = !1) {
		return e.empty ? this : He(this, e, t);
	}
	mapPos(e, t = -1, n = T.Simple) {
		let r = 0, i = 0;
		for (let a = 0; a < this.sections.length;) {
			let o = this.sections[a++], s = this.sections[a++], c = r + o;
			if (s < 0) {
				if (c > e) return i + (e - r);
				i += o;
			} else {
				if (n != T.Simple && c >= e && (n == T.TrackDel && r < e && c > e || n == T.TrackBefore && r < e || n == T.TrackAfter && c > e)) return null;
				if (c > e || c == e && t < 0 && !o) return e == r || t < 0 ? i : i + s;
				i += s;
			}
			r = c;
		}
		if (e > r) throw RangeError(`Position ${e} is out of range for changeset of length ${r}`);
		return i;
	}
	touchesRange(e, t = e) {
		for (let n = 0, r = 0; n < this.sections.length && r <= t;) {
			let i = this.sections[n++], a = this.sections[n++], o = r + i;
			if (a >= 0 && r <= t && o >= e) return r < e && o > t ? "cover" : !0;
			r = o;
		}
		return !1;
	}
	toString() {
		let e = "";
		for (let t = 0; t < this.sections.length;) {
			let n = this.sections[t++], r = this.sections[t++];
			e += (e ? " " : "") + n + (r >= 0 ? ":" + r : "");
		}
		return e;
	}
	toJSON() {
		return this.sections;
	}
	static fromJSON(t) {
		if (!Array.isArray(t) || t.length % 2 || t.some((e) => typeof e != "number")) throw RangeError("Invalid JSON representation of ChangeDesc");
		return new e(t);
	}
	static create(t) {
		return new e(t);
	}
}, ze = class e extends Re {
	constructor(e, t) {
		super(e), this.inserted = t;
	}
	apply(e) {
		if (this.length != e.length) throw RangeError("Applying change set to a document with the wrong length");
		return Ve(this, (t, n, r, i, a) => e = e.replace(r, r + (n - t), a), !1), e;
	}
	mapDesc(e, t = !1) {
		return He(this, e, t, !0);
	}
	invert(t) {
		let n = this.sections.slice(), r = [];
		for (let e = 0, i = 0; e < n.length; e += 2) {
			let a = n[e], o = n[e + 1];
			if (o >= 0) {
				n[e] = o, n[e + 1] = a;
				let s = e >> 1;
				for (; r.length < s;) r.push(C.empty);
				r.push(a ? t.slice(i, i + a) : C.empty);
			}
			i += a;
		}
		return new e(n, r);
	}
	compose(e) {
		return this.empty ? e : e.empty ? this : Ue(this, e, !0);
	}
	map(e, t = !1) {
		return e.empty ? this : He(this, e, t, !0);
	}
	iterChanges(e, t = !1) {
		Ve(this, e, t);
	}
	get desc() {
		return Re.create(this.sections);
	}
	filter(t) {
		let n = [], r = [], i = [], a = new We(this);
		done: for (let e = 0, o = 0;;) {
			let s = e == t.length ? 1e9 : t[e++];
			for (; o < s || o == s && a.len == 0;) {
				if (a.done) break done;
				let e = Math.min(a.len, s - o);
				E(i, e, -1);
				let t = a.ins == -1 ? -1 : a.off == 0 ? a.ins : 0;
				E(n, e, t), t > 0 && Be(r, n, a.text), a.forward(e), o += e;
			}
			let c = t[e++];
			for (; o < c;) {
				if (a.done) break done;
				let e = Math.min(a.len, c - o);
				E(n, e, -1), E(i, e, a.ins == -1 ? -1 : a.off == 0 ? a.ins : 0), a.forward(e), o += e;
			}
		}
		return {
			changes: new e(n, r),
			filtered: Re.create(i)
		};
	}
	toJSON() {
		let e = [];
		for (let t = 0; t < this.sections.length; t += 2) {
			let n = this.sections[t], r = this.sections[t + 1];
			r < 0 ? e.push(n) : r == 0 ? e.push([n]) : e.push([n].concat(this.inserted[t >> 1].toJSON()));
		}
		return e;
	}
	static of(t, n, r) {
		let i = [], a = [], o = 0, s = null;
		function c(t = !1) {
			if (!t && !i.length) return;
			o < n && E(i, n - o, -1);
			let r = new e(i, a);
			s = s ? s.compose(r.map(s)) : r, i = [], a = [], o = 0;
		}
		function l(t) {
			if (Array.isArray(t)) for (let e of t) l(e);
			else if (t instanceof e) {
				if (t.length != n) throw RangeError(`Mismatched change set length (got ${t.length}, expected ${n})`);
				c(), s = s ? s.compose(t.map(s)) : t;
			} else {
				let { from: e, to: s = e, insert: l } = t;
				if (e > s || e < 0 || s > n) throw RangeError(`Invalid change range ${e} to ${s} (in doc of length ${n})`);
				let u = l ? typeof l == "string" ? C.of(l.split(r || Le)) : l : C.empty, d = u.length;
				if (e == s && d == 0) return;
				e < o && c(), e > o && E(i, e - o, -1), E(i, s - e, d), Be(a, i, u), o = s;
			}
		}
		return l(t), c(!s), s;
	}
	static empty(t) {
		return new e(t ? [t, -1] : [], []);
	}
	static fromJSON(t) {
		if (!Array.isArray(t)) throw RangeError("Invalid JSON representation of ChangeSet");
		let n = [], r = [];
		for (let e = 0; e < t.length; e++) {
			let i = t[e];
			if (typeof i == "number") n.push(i, -1);
			else if (!Array.isArray(i) || typeof i[0] != "number" || i.some((e, t) => t && typeof e != "string")) throw RangeError("Invalid JSON representation of ChangeSet");
			else if (i.length == 1) n.push(i[0], 0);
			else {
				for (; r.length < e;) r.push(C.empty);
				r[e] = C.of(i.slice(1)), n.push(i[0], r[e].length);
			}
		}
		return new e(n, r);
	}
	static createSet(t, n) {
		return new e(t, n);
	}
};
function E(e, t, n, r = !1) {
	if (t == 0 && n <= 0) return;
	let i = e.length - 2;
	i >= 0 && n <= 0 && n == e[i + 1] ? e[i] += t : i >= 0 && t == 0 && e[i] == 0 ? e[i + 1] += n : r ? (e[i] += t, e[i + 1] += n) : e.push(t, n);
}
function Be(e, t, n) {
	if (n.length == 0) return;
	let r = t.length - 2 >> 1;
	if (r < e.length) e[e.length - 1] = e[e.length - 1].append(n);
	else {
		for (; e.length < r;) e.push(C.empty);
		e.push(n);
	}
}
function Ve(e, t, n) {
	let r = e.inserted;
	for (let i = 0, a = 0, o = 0; o < e.sections.length;) {
		let s = e.sections[o++], c = e.sections[o++];
		if (c < 0) i += s, a += s;
		else {
			let l = i, u = a, d = C.empty;
			for (; l += s, u += c, c && r && (d = d.append(r[o - 2 >> 1])), !(n || o == e.sections.length || e.sections[o + 1] < 0);) s = e.sections[o++], c = e.sections[o++];
			t(i, l, a, u, d), i = l, a = u;
		}
	}
}
function He(e, t, n, r = !1) {
	let i = [], a = r ? [] : null, o = new We(e), s = new We(t);
	for (let e = -1;;) if (o.done && s.len || s.done && o.len) throw Error("Mismatched change set lengths");
	else if (o.ins == -1 && s.ins == -1) {
		let e = Math.min(o.len, s.len);
		E(i, e, -1), o.forward(e), s.forward(e);
	} else if (s.ins >= 0 && (o.ins < 0 || e == o.i || o.off == 0 && (s.len < o.len || s.len == o.len && !n))) {
		let t = s.len;
		for (E(i, s.ins, -1); t;) {
			let n = Math.min(o.len, t);
			o.ins >= 0 && e < o.i && o.len <= n && (E(i, 0, o.ins), a && Be(a, i, o.text), e = o.i), o.forward(n), t -= n;
		}
		s.next();
	} else if (o.ins >= 0) {
		let t = 0, n = o.len;
		for (; n;) if (s.ins == -1) {
			let e = Math.min(n, s.len);
			t += e, n -= e, s.forward(e);
		} else if (s.ins == 0 && s.len < n) n -= s.len, s.next();
		else break;
		E(i, t, e < o.i ? o.ins : 0), a && e < o.i && Be(a, i, o.text), e = o.i, o.forward(o.len - n);
	} else if (o.done && s.done) return a ? ze.createSet(i, a) : Re.create(i);
	else throw Error("Mismatched change set lengths");
}
function Ue(e, t, n = !1) {
	let r = [], i = n ? [] : null, a = new We(e), o = new We(t);
	for (let e = !1;;) if (a.done && o.done) return i ? ze.createSet(r, i) : Re.create(r);
	else if (a.ins == 0) E(r, a.len, 0, e), a.next();
	else if (o.len == 0 && !o.done) E(r, 0, o.ins, e), i && Be(i, r, o.text), o.next();
	else if (a.done || o.done) throw Error("Mismatched change set lengths");
	else {
		let t = Math.min(a.len2, o.len), n = r.length;
		if (a.ins == -1) {
			let n = o.ins == -1 ? -1 : o.off ? 0 : o.ins;
			E(r, t, n, e), i && n && Be(i, r, o.text);
		} else o.ins == -1 ? (E(r, a.off ? 0 : a.len, t, e), i && Be(i, r, a.textBit(t))) : (E(r, a.off ? 0 : a.len, o.off ? 0 : o.ins, e), i && !o.off && Be(i, r, o.text));
		e = (a.ins > t || o.ins >= 0 && o.len > t) && (e || r.length > n), a.forward2(t), o.forward(t);
	}
}
var We = class {
	constructor(e) {
		this.set = e, this.i = 0, this.next();
	}
	next() {
		let { sections: e } = this.set;
		this.i < e.length ? (this.len = e[this.i++], this.ins = e[this.i++]) : (this.len = 0, this.ins = -2), this.off = 0;
	}
	get done() {
		return this.ins == -2;
	}
	get len2() {
		return this.ins < 0 ? this.len : this.ins;
	}
	get text() {
		let { inserted: e } = this.set, t = this.i - 2 >> 1;
		return t >= e.length ? C.empty : e[t];
	}
	textBit(e) {
		let { inserted: t } = this.set, n = this.i - 2 >> 1;
		return n >= t.length && !e ? C.empty : t[n].slice(this.off, e == null ? void 0 : this.off + e);
	}
	forward(e) {
		e == this.len ? this.next() : (this.len -= e, this.off += e);
	}
	forward2(e) {
		this.ins == -1 ? this.forward(e) : e == this.ins ? this.next() : (this.ins -= e, this.off += e);
	}
}, Ge = class e {
	constructor(e, t, n, r) {
		this.from = e, this.to = t, this.flags = n, this.goalColumn = r;
	}
	get anchor() {
		return this.flags & 32 ? this.to : this.from;
	}
	get head() {
		return this.flags & 32 ? this.from : this.to;
	}
	get empty() {
		return this.from == this.to;
	}
	get assoc() {
		return this.flags & 8 ? -1 : this.flags & 16 ? 1 : 0;
	}
	get undirectional() {
		return (this.flags & 64) > 0;
	}
	get bidiLevel() {
		let e = this.flags & 7;
		return e == 7 ? null : e;
	}
	map(t, n = -1) {
		let r, i;
		return this.empty ? r = i = t.mapPos(this.from, n) : (r = t.mapPos(this.from, 1), i = t.mapPos(this.to, -1)), r == this.from && i == this.to ? this : new e(r, i, this.flags, this.goalColumn);
	}
	extend(e, t = e, n = 0) {
		if (e <= this.anchor && t >= this.anchor) return D.range(e, t, void 0, void 0, n);
		let r = Math.abs(e - this.anchor) > Math.abs(t - this.anchor) ? e : t;
		return D.range(this.anchor, r, void 0, void 0, n);
	}
	eq(e, t = !1) {
		return this.anchor == e.anchor && this.head == e.head && this.goalColumn == e.goalColumn && (!t || !this.empty || this.assoc == e.assoc);
	}
	toJSON() {
		return {
			anchor: this.anchor,
			head: this.head
		};
	}
	static fromJSON(e) {
		if (!e || typeof e.anchor != "number" || typeof e.head != "number") throw RangeError("Invalid JSON representation for SelectionRange");
		return D.range(e.anchor, e.head);
	}
	static create(t, n, r, i) {
		return new e(t, n, r, i);
	}
}, D = class e {
	constructor(e, t) {
		this.ranges = e, this.mainIndex = t;
	}
	map(t, n = -1) {
		return t.empty ? this : e.create(this.ranges.map((e) => e.map(t, n)), this.mainIndex);
	}
	eq(e, t = !1) {
		if (this.ranges.length != e.ranges.length || this.mainIndex != e.mainIndex) return !1;
		for (let n = 0; n < this.ranges.length; n++) if (!this.ranges[n].eq(e.ranges[n], t)) return !1;
		return !0;
	}
	get main() {
		return this.ranges[this.mainIndex];
	}
	asSingle() {
		return this.ranges.length == 1 ? this : new e([this.main], 0);
	}
	addRange(t, n = !0) {
		return e.create([t].concat(this.ranges), n ? 0 : this.mainIndex + 1);
	}
	replaceRange(t, n = this.mainIndex) {
		let r = this.ranges.slice();
		return r[n] = t, e.create(r, this.mainIndex);
	}
	toJSON() {
		return {
			ranges: this.ranges.map((e) => e.toJSON()),
			main: this.mainIndex
		};
	}
	static fromJSON(t) {
		if (!t || !Array.isArray(t.ranges) || typeof t.main != "number" || t.main >= t.ranges.length) throw RangeError("Invalid JSON representation for EditorSelection");
		return new e(t.ranges.map((e) => Ge.fromJSON(e)), t.main);
	}
	static single(t, n = t) {
		return new e([e.range(t, n)], 0);
	}
	static create(t, n = 0) {
		if (t.length == 0) throw RangeError("A selection needs at least one range");
		for (let r = 0, i = 0; i < t.length; i++) {
			let a = t[i];
			if (a.empty ? a.from <= r : a.from < r) return e.normalized(t.slice(), n);
			r = a.to;
		}
		return new e(t, n);
	}
	static cursor(e, t = 0, n, r) {
		return Ge.create(e, e, (t == 0 ? 0 : t < 0 ? 8 : 16) | (n == null ? 7 : Math.min(6, n)), r);
	}
	static range(e, t, n, r, i) {
		let a = r == null ? 7 : Math.min(6, r);
		return !i && e != t && (i = t < e ? 1 : -1), i && (a |= i < 0 ? 8 : 16), t < e ? Ge.create(t, e, a | 32, n) : Ge.create(e, t, a, n);
	}
	static undirectionalRange(e, t) {
		return Ge.create(e, t, 64, void 0);
	}
	static normalized(t, n = 0) {
		let r = t[n];
		t.sort((e, t) => e.from - t.from), n = t.indexOf(r);
		for (let r = 1; r < t.length; r++) {
			let i = t[r], a = t[r - 1];
			if (i.empty ? i.from <= a.to : i.from < a.to) {
				let o = a.from, s = Math.max(i.to, a.to);
				r <= n && n--, t.splice(--r, 2, i.anchor > i.head ? e.range(s, o) : e.range(o, s));
			}
		}
		return new e(t, n);
	}
};
function Ke(e, t) {
	for (let n of e.ranges) if (n.to > t) throw RangeError("Selection points outside of document");
}
var qe = 0, O = class e {
	constructor(e, t, n, r, i) {
		this.combine = e, this.compareInput = t, this.compare = n, this.isStatic = r, this.id = qe++, this.default = e([]), this.extensions = typeof i == "function" ? i(this) : i;
	}
	get reader() {
		return this;
	}
	static define(t = {}) {
		return new e(t.combine || ((e) => e), t.compareInput || ((e, t) => e === t), t.compare || (t.combine ? (e, t) => e === t : Je), !!t.static, t.enables);
	}
	of(e) {
		return new Ye([], this, 0, e);
	}
	compute(e, t) {
		if (this.isStatic) throw Error("Can't compute a static facet");
		return new Ye(e, this, 1, t);
	}
	computeN(e, t) {
		if (this.isStatic) throw Error("Can't compute a static facet");
		return new Ye(e, this, 2, t);
	}
	from(e, t) {
		return t || (t = (e) => e), this.compute([e], (n) => t(n.field(e)));
	}
};
function Je(e, t) {
	return e == t || e.length == t.length && e.every((e, n) => e === t[n]);
}
var Ye = class {
	constructor(e, t, n, r) {
		this.dependencies = e, this.facet = t, this.type = n, this.value = r, this.id = qe++;
	}
	dynamicSlot(e) {
		var t;
		let n = this.value, r = this.facet.compareInput, i = this.id, a = e[i] >> 1, o = this.type == 2, s = !1, c = !1, l = [];
		for (let n of this.dependencies) n == "doc" ? s = !0 : n == "selection" ? c = !0 : ((t = e[n.id]) == null ? 1 : t) & 1 || l.push(e[n.id]);
		return {
			create(e) {
				return e.values[a] = n(e), 1;
			},
			update(e, t) {
				if (s && t.docChanged || c && (t.docChanged || t.selection) || Ze(e, l)) {
					let t = n(e);
					if (o ? !Xe(t, e.values[a], r) : !r(t, e.values[a])) return e.values[a] = t, 1;
				}
				return 0;
			},
			reconfigure: (e, t) => {
				let s, c = t.config.address[i];
				if (c != null) {
					let i = lt(t, c);
					if (this.dependencies.every((n) => n instanceof O ? t.facet(n) === e.facet(n) : n instanceof k ? t.field(n, !1) == e.field(n, !1) : !0) || (o ? Xe(s = n(e), i, r) : r(s = n(e), i))) return e.values[a] = i, 0;
				} else s = n(e);
				return e.values[a] = s, 1;
			}
		};
	}
	get extension() {
		return this;
	}
};
function Xe(e, t, n) {
	if (e.length != t.length) return !1;
	for (let r = 0; r < e.length; r++) if (!n(e[r], t[r])) return !1;
	return !0;
}
function Ze(e, t) {
	let n = !1;
	for (let r of t) ct(e, r) & 1 && (n = !0);
	return n;
}
function Qe(e, t, n) {
	let r = n.map((t) => e[t.id]), i = n.map((e) => e.type), a = r.filter((e) => !(e & 1)), o = e[t.id] >> 1;
	function s(e) {
		let n = [];
		for (let t = 0; t < r.length; t++) {
			let a = lt(e, r[t]);
			if (i[t] == 2) for (let e of a) n.push(e);
			else n.push(a);
		}
		return t.combine(n);
	}
	return {
		create(e) {
			for (let t of r) ct(e, t);
			return e.values[o] = s(e), 1;
		},
		update(e, n) {
			if (!Ze(e, a)) return 0;
			let r = s(e);
			return t.compare(r, e.values[o]) ? 0 : (e.values[o] = r, 1);
		},
		reconfigure(e, i) {
			let a = Ze(e, r), c = i.config.facets[t.id], l = i.facet(t);
			if (c && !a && Je(n, c)) return e.values[o] = l, 0;
			let u = s(e);
			return t.compare(u, l) ? (e.values[o] = l, 0) : (e.values[o] = u, 1);
		}
	};
}
var $e = /*@__PURE__*/ O.define({ static: !0 }), k = class e {
	constructor(e, t, n, r, i) {
		this.id = e, this.createF = t, this.updateF = n, this.compareF = r, this.spec = i, this.provides = void 0;
	}
	static define(t) {
		let n = new e(qe++, t.create, t.update, t.compare || ((e, t) => e === t), t);
		return t.provide && (n.provides = t.provide(n)), n;
	}
	create(e) {
		let t = e.facet($e).find((e) => e.field == this);
		return ((t == null ? void 0 : t.create) || this.createF)(e);
	}
	slot(e) {
		let t = e[this.id] >> 1;
		return {
			create: (e) => (e.values[t] = this.create(e), 1),
			update: (e, n) => {
				let r = e.values[t], i = this.updateF(r, n);
				return this.compareF(r, i) ? 0 : (e.values[t] = i, 1);
			},
			reconfigure: (e, n) => {
				let r = e.facet($e), i = n.facet($e), a;
				return (a = r.find((e) => e.field == this)) && a != i.find((e) => e.field == this) ? (e.values[t] = a.create(e), 1) : n.config.address[this.id] == null ? (e.values[t] = this.create(e), 1) : (e.values[t] = n.field(this), 0);
			}
		};
	}
	init(e) {
		return [this, $e.of({
			field: this,
			create: e
		})];
	}
	get extension() {
		return this;
	}
}, et = {
	lowest: 4,
	low: 3,
	default: 2,
	high: 1,
	highest: 0
};
function tt(e) {
	return (t) => new rt(t, e);
}
var nt = {
	highest: /*@__PURE__*/ tt(et.highest),
	high: /*@__PURE__*/ tt(et.high),
	default: /*@__PURE__*/ tt(et.default),
	low: /*@__PURE__*/ tt(et.low),
	lowest: /*@__PURE__*/ tt(et.lowest)
}, rt = class {
	constructor(e, t) {
		this.inner = e, this.prec = t;
	}
	get extension() {
		return this;
	}
}, it = class e {
	of(e) {
		return new at(this, e);
	}
	reconfigure(t) {
		return e.reconfigure.of({
			compartment: this,
			extension: t
		});
	}
	get(e) {
		return e.config.compartments.get(this);
	}
}, at = class {
	constructor(e, t) {
		this.compartment = e, this.inner = t;
	}
	get extension() {
		return this;
	}
}, ot = class e {
	constructor(e, t, n, r, i, a) {
		for (this.base = e, this.compartments = t, this.dynamicSlots = n, this.address = r, this.staticValues = i, this.facets = a, this.statusTemplate = []; this.statusTemplate.length < n.length;) this.statusTemplate.push(0);
	}
	staticFacet(e) {
		let t = this.address[e.id];
		return t == null ? e.default : this.staticValues[t >> 1];
	}
	static resolve(t, n, r) {
		let i = [], a = Object.create(null), o = /* @__PURE__ */ new Map();
		for (let e of st(t, n, o)) e instanceof k ? i.push(e) : (a[e.facet.id] || (a[e.facet.id] = [])).push(e);
		let s = Object.create(null), c = [], l = [];
		for (let e of i) s[e.id] = l.length << 1, l.push((t) => e.slot(t));
		let u = r == null ? void 0 : r.config.facets;
		for (let e in a) {
			let t = a[e], n = t[0].facet, i = u && u[e] || [];
			if (t.every((e) => e.type == 0)) {
				if (s[n.id] = c.length << 1 | 1, Je(i, t)) c.push(r.facet(n));
				else {
					let e = n.combine(t.map((e) => e.value));
					c.push(r && n.compare(e, r.facet(n)) ? r.facet(n) : e);
				}
			} else {
				for (let e of t) e.type == 0 ? (s[e.id] = c.length << 1 | 1, c.push(e.value)) : (s[e.id] = l.length << 1, l.push((t) => e.dynamicSlot(t)));
				s[n.id] = l.length << 1, l.push((e) => Qe(e, n, t));
			}
		}
		let d = l.map((e) => e(s));
		return new e(t, o, d, s, c, a);
	}
};
function st(e, t, n) {
	let r = [
		[],
		[],
		[],
		[],
		[]
	], i = /* @__PURE__ */ new Map();
	function a(e, o) {
		let s = i.get(e);
		if (s != null) {
			if (s <= o) return;
			let t = r[s].indexOf(e);
			t > -1 && r[s].splice(t, 1), e instanceof at && n.delete(e.compartment);
		}
		if (i.set(e, o), Array.isArray(e)) for (let t of e) a(t, o);
		else if (e instanceof at) {
			if (n.has(e.compartment)) throw RangeError("Duplicate use of compartment in extensions");
			let r = t.get(e.compartment) || e.inner;
			n.set(e.compartment, r), a(r, o);
		} else if (e instanceof rt) a(e.inner, e.prec);
		else if (e instanceof k) r[o].push(e), e.provides && a(e.provides, o);
		else if (e instanceof Ye) r[o].push(e), e.facet.extensions && a(e.facet.extensions, et.default);
		else {
			let t = e.extension;
			if (!t) throw Error(`Unrecognized extension value in extension set (${e}).`);
			if (t == e) throw Error(`Unrecognized extension value in extension set (${e}). This sometimes happens because multiple instances of @codemirror/state are loaded, breaking instanceof checks.`);
			a(t, o);
		}
	}
	return a(e, et.default), r.reduce((e, t) => e.concat(t));
}
function ct(e, t) {
	if (t & 1) return 2;
	let n = t >> 1, r = e.status[n];
	if (r == 4) throw Error("Cyclic dependency between fields and/or facets");
	if (r & 2) return r;
	e.status[n] = 4;
	let i = e.computeSlot(e, e.config.dynamicSlots[n]);
	return e.status[n] = 2 | i;
}
function lt(e, t) {
	return t & 1 ? e.config.staticValues[t >> 1] : e.values[t >> 1];
}
var ut = /*@__PURE__*/ O.define(), dt = /*@__PURE__*/ O.define({
	combine: (e) => e.some((e) => e),
	static: !0
}), ft = /*@__PURE__*/ O.define({
	combine: (e) => e.length ? e[0] : void 0,
	static: !0
}), pt = /*@__PURE__*/ O.define(), mt = /*@__PURE__*/ O.define(), ht = /*@__PURE__*/ O.define(), gt = /*@__PURE__*/ O.define({ combine: (e) => e.length ? e[0] : !1 }), _t = class {
	constructor(e, t) {
		this.type = e, this.value = t;
	}
	static define() {
		return new vt();
	}
}, vt = class {
	of(e) {
		return new _t(this, e);
	}
}, yt = class {
	constructor(e) {
		this.map = e;
	}
	of(e) {
		return new A(this, e);
	}
}, A = class e {
	constructor(e, t) {
		this.type = e, this.value = t;
	}
	map(t) {
		let n = this.type.map(this.value, t);
		return n === void 0 ? void 0 : n == this.value ? this : new e(this.type, n);
	}
	is(e) {
		return this.type == e;
	}
	static define(e = {}) {
		return new yt(e.map || ((e) => e));
	}
	static mapEffects(e, t) {
		if (!e.length) return e;
		let n = [];
		for (let r of e) {
			let e = r.map(t);
			e && n.push(e);
		}
		return n;
	}
};
A.reconfigure = /*@__PURE__*/ A.define(), A.appendConfig = /*@__PURE__*/ A.define();
var j = class e {
	constructor(t, n, r, i, a, o) {
		this.startState = t, this.changes = n, this.selection = r, this.effects = i, this.annotations = a, this.scrollIntoView = o, this._doc = null, this._state = null, r && Ke(r, n.newLength), a.some((t) => t.type == e.time) || (this.annotations = a.concat(e.time.of(Date.now())));
	}
	static create(t, n, r, i, a, o) {
		return new e(t, n, r, i, a, o);
	}
	get newDoc() {
		return this._doc || (this._doc = this.changes.apply(this.startState.doc));
	}
	get newSelection() {
		return this.selection || this.startState.selection.map(this.changes);
	}
	get state() {
		return this._state || this.startState.applyTransaction(this), this._state;
	}
	annotation(e) {
		for (let t of this.annotations) if (t.type == e) return t.value;
	}
	get docChanged() {
		return !this.changes.empty;
	}
	get reconfigured() {
		return this.startState.config != this.state.config;
	}
	isUserEvent(t) {
		let n = this.annotation(e.userEvent);
		return !!(n && (n == t || n.length > t.length && n.slice(0, t.length) == t && n[t.length] == "."));
	}
};
j.time = /*@__PURE__*/ _t.define(), j.userEvent = /*@__PURE__*/ _t.define(), j.addToHistory = /*@__PURE__*/ _t.define(), j.remote = /*@__PURE__*/ _t.define();
function bt(e, t) {
	let n = [];
	for (let r = 0, i = 0;;) {
		let a, o;
		if (r < e.length && (i == t.length || t[i] >= e[r])) a = e[r++], o = e[r++];
		else if (i < t.length) a = t[i++], o = t[i++];
		else return n;
		!n.length || n[n.length - 1] < a ? n.push(a, o) : n[n.length - 1] < o && (n[n.length - 1] = o);
	}
}
function xt(e, t, n) {
	var r;
	let i, a, o;
	return n ? (i = t.changes, a = ze.empty(t.changes.length), o = e.changes.compose(t.changes)) : (i = t.changes.map(e.changes), a = e.changes.mapDesc(t.changes, !0), o = e.changes.compose(i)), {
		changes: o,
		selection: t.selection ? t.selection.map(a) : (r = e.selection) == null ? void 0 : r.map(i),
		effects: A.mapEffects(e.effects, i).concat(A.mapEffects(t.effects, a)),
		annotations: e.annotations.length ? e.annotations.concat(t.annotations) : t.annotations,
		scrollIntoView: e.scrollIntoView || t.scrollIntoView
	};
}
function St(e, t, n) {
	let r = t.selection, i = Dt(t.annotations);
	return t.userEvent && (i = i.concat(j.userEvent.of(t.userEvent))), {
		changes: t.changes instanceof ze ? t.changes : ze.of(t.changes || [], n, e.facet(ft)),
		selection: r && (r instanceof D ? r : D.single(r.anchor, r.head)),
		effects: Dt(t.effects),
		annotations: i,
		scrollIntoView: !!t.scrollIntoView
	};
}
function Ct(e, t, n) {
	let r = St(e, t.length ? t[0] : {}, e.doc.length);
	t.length && t[0].filter === !1 && (n = !1);
	for (let i = 1; i < t.length; i++) {
		t[i].filter === !1 && (n = !1);
		let a = !!t[i].sequential;
		r = xt(r, St(e, t[i], a ? r.changes.newLength : e.doc.length), a);
	}
	let i = j.create(e, r.changes, r.selection, r.effects, r.annotations, r.scrollIntoView);
	return Tt(n ? wt(i) : i);
}
function wt(e) {
	let t = e.startState, n = !0;
	for (let r of t.facet(pt)) {
		let t = r(e);
		if (t === !1) {
			n = !1;
			break;
		}
		Array.isArray(t) && (n = n === !0 ? t : bt(n, t));
	}
	if (n !== !0) {
		let r, i;
		if (n === !1) i = e.changes.invertedDesc, r = ze.empty(t.doc.length);
		else {
			let t = e.changes.filter(n);
			r = t.changes, i = t.filtered.mapDesc(t.changes).invertedDesc;
		}
		e = j.create(t, r, e.selection && e.selection.map(i), A.mapEffects(e.effects, i), e.annotations, e.scrollIntoView);
	}
	let r = t.facet(mt);
	for (let n = r.length - 1; n >= 0; n--) {
		let i = r[n](e);
		e = i instanceof j ? i : Array.isArray(i) && i.length == 1 && i[0] instanceof j ? i[0] : Ct(t, Dt(i), !1);
	}
	return e;
}
function Tt(e) {
	let t = e.startState, n = t.facet(ht), r = e;
	for (let i = n.length - 1; i >= 0; i--) {
		let a = n[i](e);
		a && Object.keys(a).length && (r = xt(r, St(t, a, e.changes.newLength), !0));
	}
	return r == e ? e : j.create(t, e.changes, e.selection, r.effects, r.annotations, r.scrollIntoView);
}
var Et = [];
function Dt(e) {
	return e == null ? Et : Array.isArray(e) ? e : [e];
}
var M = /*@__PURE__*/ (function(e) {
	return e[e.Word = 0] = "Word", e[e.Space = 1] = "Space", e[e.Other = 2] = "Other", e;
})(M || (M = {})), Ot = /[\u00df\u0587\u0590-\u05f4\u0600-\u06ff\u3040-\u309f\u30a0-\u30ff\u3400-\u4db5\u4e00-\u9fcc\uac00-\ud7af]/, kt;
try {
	kt = /*@__PURE__*/ RegExp("[\\p{Alphabetic}\\p{Number}_]", "u");
} catch (e) {}
function At(e) {
	if (kt) return kt.test(e);
	for (let t = 0; t < e.length; t++) {
		let n = e[t];
		if (/\w/.test(n) || n > "" && (n.toUpperCase() != n.toLowerCase() || Ot.test(n))) return !0;
	}
	return !1;
}
function jt(e) {
	return (t) => {
		if (!/\S/.test(t)) return M.Space;
		if (At(t)) return M.Word;
		for (let n = 0; n < e.length; n++) if (t.indexOf(e[n]) > -1) return M.Word;
		return M.Other;
	};
}
var N = class e {
	constructor(e, t, n, r, i, a) {
		this.config = e, this.doc = t, this.selection = n, this.values = r, this.status = e.statusTemplate.slice(), this.computeSlot = i, a && (a._state = this);
		for (let e = 0; e < this.config.dynamicSlots.length; e++) ct(this, e << 1);
		this.computeSlot = null;
	}
	field(e, t = !0) {
		let n = this.config.address[e.id];
		if (n == null) {
			if (t) throw RangeError("Field is not present in this state");
			return;
		}
		return ct(this, n), lt(this, n);
	}
	update(...e) {
		return Ct(this, e, !0);
	}
	applyTransaction(t) {
		let n = this.config, { base: r, compartments: i } = n;
		for (let e of t.effects) e.is(it.reconfigure) ? (n && (i = /* @__PURE__ */ new Map(), n.compartments.forEach((e, t) => i.set(t, e)), n = null), i.set(e.value.compartment, e.value.extension)) : e.is(A.reconfigure) ? (n = null, r = e.value) : e.is(A.appendConfig) && (n = null, r = Dt(r).concat(e.value));
		let a;
		n ? a = t.startState.values.slice() : (n = ot.resolve(r, i, this), a = new e(n, this.doc, this.selection, n.dynamicSlots.map(() => null), (e, t) => t.reconfigure(e, this), null).values);
		let o = t.startState.facet(dt) ? t.newSelection : t.newSelection.asSingle();
		new e(n, t.newDoc, o, a, (e, n) => n.update(e, t), t);
	}
	replaceSelection(e) {
		return typeof e == "string" && (e = this.toText(e)), this.changeByRange((t) => ({
			changes: {
				from: t.from,
				to: t.to,
				insert: e
			},
			range: D.cursor(t.from + e.length)
		}));
	}
	changeByRange(e) {
		let t = this.selection, n = e(t.ranges[0]), r = this.changes(n.changes), i = [n.range], a = Dt(n.effects);
		for (let n = 1; n < t.ranges.length; n++) {
			let o = e(t.ranges[n]), s = this.changes(o.changes), c = s.map(r);
			for (let e = 0; e < n; e++) i[e] = i[e].map(c);
			let l = r.mapDesc(s, !0);
			i.push(o.range.map(l)), r = r.compose(c), a = A.mapEffects(a, c).concat(A.mapEffects(Dt(o.effects), l));
		}
		return {
			changes: r,
			selection: D.create(i, t.mainIndex),
			effects: a
		};
	}
	changes(t = []) {
		return t instanceof ze ? t : ze.of(t, this.doc.length, this.facet(e.lineSeparator));
	}
	toText(t) {
		return C.of(t.split(this.facet(e.lineSeparator) || Le));
	}
	sliceDoc(e = 0, t = this.doc.length) {
		return this.doc.sliceString(e, t, this.lineBreak);
	}
	facet(e) {
		let t = this.config.address[e.id];
		return t == null ? e.default : (ct(this, t), lt(this, t));
	}
	toJSON(e) {
		let t = {
			doc: this.sliceDoc(),
			selection: this.selection.toJSON()
		};
		if (e) for (let n in e) {
			let r = e[n];
			r instanceof k && this.config.address[r.id] != null && (t[n] = r.spec.toJSON(this.field(e[n]), this));
		}
		return t;
	}
	static fromJSON(t, n = {}, r) {
		if (!t || typeof t.doc != "string") throw RangeError("Invalid JSON representation for EditorState");
		let i = [];
		if (r) {
			for (let e in r) if (Object.prototype.hasOwnProperty.call(t, e)) {
				let n = r[e], a = t[e];
				i.push(n.init((e) => n.spec.fromJSON(a, e)));
			}
		}
		return e.create({
			doc: t.doc,
			selection: D.fromJSON(t.selection),
			extensions: n.extensions ? i.concat([n.extensions]) : i
		});
	}
	static create(t = {}) {
		let n = ot.resolve(t.extensions || [], /* @__PURE__ */ new Map()), r = t.doc instanceof C ? t.doc : C.of((t.doc || "").split(n.staticFacet(e.lineSeparator) || Le)), i = t.selection ? t.selection instanceof D ? t.selection : D.single(t.selection.anchor, t.selection.head) : D.single(0);
		return Ke(i, r.length), n.staticFacet(dt) || (i = i.asSingle()), new e(n, r, i, n.dynamicSlots.map(() => null), (e, t) => t.create(e), null);
	}
	get tabSize() {
		return this.facet(e.tabSize);
	}
	get lineBreak() {
		return this.facet(e.lineSeparator) || "\n";
	}
	get readOnly() {
		return this.facet(gt);
	}
	phrase(t, ...n) {
		for (let n of this.facet(e.phrases)) if (Object.prototype.hasOwnProperty.call(n, t)) {
			t = n[t];
			break;
		}
		return n.length && (t = t.replace(/\$(\$|\d*)/g, (e, t) => {
			if (t == "$") return "$";
			let r = +(t || 1);
			return !r || r > n.length ? e : n[r - 1];
		})), t;
	}
	languageDataAt(e, t, n = -1) {
		let r = [];
		for (let i of this.facet(ut)) for (let a of i(this, t, n)) Object.prototype.hasOwnProperty.call(a, e) && r.push(a[e]);
		return r;
	}
	charCategorizer(e) {
		let t = this.languageDataAt("wordChars", e);
		return jt(t.length ? t[0] : "");
	}
	wordAt(e) {
		let { text: t, from: n, length: r } = this.doc.lineAt(e), i = this.charCategorizer(e), a = e - n, o = e - n;
		for (; a > 0;) {
			let e = w(t, a, !1);
			if (i(t.slice(e, a)) != M.Word) break;
			a = e;
		}
		for (; o < r;) {
			let e = w(t, o);
			if (i(t.slice(o, e)) != M.Word) break;
			o = e;
		}
		return a == o ? null : D.range(a + n, o + n);
	}
};
N.allowMultipleSelections = dt, N.tabSize = /*@__PURE__*/ O.define({ combine: (e) => e.length ? e[0] : 4 }), N.lineSeparator = ft, N.readOnly = gt, N.phrases = /*@__PURE__*/ O.define({ compare(e, t) {
	let n = Object.keys(e), r = Object.keys(t);
	return n.length == r.length && n.every((n) => e[n] == t[n]);
} }), N.languageData = ut, N.changeFilter = pt, N.transactionFilter = mt, N.transactionExtender = ht, it.reconfigure = /*@__PURE__*/ A.define();
function Mt(e, t, n = {}) {
	let r = {};
	for (let t of e) for (let e of Object.keys(t)) {
		let i = t[e], a = r[e];
		if (a === void 0) r[e] = i;
		else if (a !== i && i !== void 0) {
			if (Object.hasOwnProperty.call(n, e)) r[e] = n[e](a, i);
			else throw Error("Config merge conflict for field " + e);
		}
	}
	for (let e in t) r[e] === void 0 && (r[e] = t[e]);
	return r;
}
var Nt = class {
	eq(e) {
		return this == e;
	}
	range(e, t = e) {
		return Ft.create(e, t, this);
	}
};
Nt.prototype.startSide = Nt.prototype.endSide = 0, Nt.prototype.point = !1, Nt.prototype.mapMode = T.TrackDel;
function Pt(e, t) {
	return e == t || e.constructor == t.constructor && e.eq(t);
}
var Ft = class e {
	constructor(e, t, n) {
		this.from = e, this.to = t, this.value = n;
	}
	static create(t, n, r) {
		return new e(t, n, r);
	}
};
function It(e, t) {
	return e.from - t.from || e.value.startSide - t.value.startSide;
}
var Lt = class e {
	constructor(e, t, n, r) {
		this.from = e, this.to = t, this.value = n, this.maxPoint = r;
	}
	get length() {
		return this.to[this.to.length - 1];
	}
	findIndex(e, t, n, r = 0) {
		let i = n ? this.to : this.from;
		for (let a = r, o = i.length;;) {
			if (a == o) return a;
			let r = a + o >> 1, s = i[r] - e || (n ? this.value[r].endSide : this.value[r].startSide) - t;
			if (r == a) return s >= 0 ? a : o;
			s >= 0 ? o = r : a = r + 1;
		}
	}
	between(e, t, n, r) {
		for (let i = this.findIndex(t, -1e9, !0), a = this.findIndex(n, 1e9, !1, i); i < a; i++) if (r(this.from[i] + e, this.to[i] + e, this.value[i]) === !1) return !1;
	}
	map(t, n) {
		let r = [], i = [], a = [], o = -1, s = -1;
		for (let e = 0; e < this.value.length; e++) {
			let c = this.value[e], l = this.from[e] + t, u = this.to[e] + t, d, f;
			if (l == u) {
				let e = n.mapPos(l, c.startSide, c.mapMode);
				if (e == null || (d = f = e, c.startSide != c.endSide && (f = n.mapPos(l, c.endSide), f < d))) continue;
			} else if (d = n.mapPos(l, c.startSide), f = n.mapPos(u, c.endSide), d > f || d == f && c.startSide > 0 && c.endSide <= 0) continue;
			(f - d || c.endSide - c.startSide) < 0 || (o < 0 && (o = d), c.point && (s = Math.max(s, f - d)), r.push(c), i.push(d - o), a.push(f - o));
		}
		return {
			mapped: r.length ? new e(i, a, r, s) : null,
			pos: o
		};
	}
}, P = class e {
	constructor(e, t, n, r) {
		this.chunkPos = e, this.chunk = t, this.nextLayer = n, this.maxPoint = r;
	}
	static create(t, n, r, i) {
		return new e(t, n, r, i);
	}
	get length() {
		let e = this.chunk.length - 1;
		return e < 0 ? 0 : Math.max(this.chunkEnd(e), this.nextLayer.length);
	}
	get size() {
		if (this.isEmpty) return 0;
		let e = this.nextLayer.size;
		for (let t of this.chunk) e += t.value.length;
		return e;
	}
	chunkEnd(e) {
		return this.chunkPos[e] + this.chunk[e].length;
	}
	update(t) {
		let { add: n = [], sort: r = !1, filterFrom: i = 0, filterTo: a = this.length } = t, o = t.filter;
		if (n.length == 0 && !o) return this;
		if (r && (n = n.slice().sort(It)), this.isEmpty) return n.length ? e.of(n) : this;
		let s = new Vt(this, null, -1).goto(0), c = 0, l = [], u = new zt();
		for (; s.value || c < n.length;) if (c < n.length && (s.from - n[c].from || s.startSide - n[c].value.startSide) >= 0) {
			let e = n[c++];
			u.addInner(e.from, e.to, e.value) || l.push(e);
		} else s.rangeIndex == 1 && s.chunkIndex < this.chunk.length && (c == n.length || this.chunkEnd(s.chunkIndex) < n[c].from) && (!o || i > this.chunkEnd(s.chunkIndex) || a < this.chunkPos[s.chunkIndex]) && u.addChunk(this.chunkPos[s.chunkIndex], this.chunk[s.chunkIndex]) ? s.nextChunk() : ((!o || i > s.to || a < s.from || o(s.from, s.to, s.value)) && (u.addInner(s.from, s.to, s.value) || l.push(Ft.create(s.from, s.to, s.value))), s.next());
		return u.finishInner(this.nextLayer.isEmpty && !l.length ? e.empty : this.nextLayer.update({
			add: l,
			filter: o,
			filterFrom: i,
			filterTo: a
		}));
	}
	map(t) {
		if (t.empty || this.isEmpty) return this;
		let n = [], r = [], i = -1;
		for (let e = 0; e < this.chunk.length; e++) {
			let a = this.chunkPos[e], o = this.chunk[e], s = t.touchesRange(a, a + o.length);
			if (s === !1) i = Math.max(i, o.maxPoint), n.push(o), r.push(t.mapPos(a));
			else if (s === !0) {
				let { mapped: e, pos: s } = o.map(a, t);
				e && (i = Math.max(i, e.maxPoint), n.push(e), r.push(s));
			}
		}
		let a = this.nextLayer.map(t);
		return n.length == 0 ? a : new e(r, n, a || e.empty, i);
	}
	between(e, t, n) {
		if (!this.isEmpty) {
			for (let r = 0; r < this.chunk.length; r++) {
				let i = this.chunkPos[r], a = this.chunk[r];
				if (t >= i && e <= i + a.length && a.between(i, e - i, t - i, n) === !1) return;
			}
			this.nextLayer.between(e, t, n);
		}
	}
	iter(e = 0) {
		return Ht.from([this]).goto(e);
	}
	get isEmpty() {
		return this.nextLayer == this;
	}
	static iter(e, t = 0) {
		return Ht.from(e).goto(t);
	}
	static compare(e, t, n, r, i = -1) {
		let a = e.filter((e) => e.maxPoint > 0 || !e.isEmpty && e.maxPoint >= i), o = t.filter((e) => e.maxPoint > 0 || !e.isEmpty && e.maxPoint >= i), s = Bt(a, o, n), c = new Wt(a, s, i), l = new Wt(o, s, i);
		n.iterGaps((e, t, n) => Gt(c, e, l, t, n, r)), n.empty && n.length == 0 && Gt(c, 0, l, 0, 0, r);
	}
	static eq(e, t, n = 0, r) {
		r == null && (r = 1e9 - 1);
		let i = e.filter((e) => !e.isEmpty && t.indexOf(e) < 0), a = t.filter((t) => !t.isEmpty && e.indexOf(t) < 0);
		if (i.length != a.length) return !1;
		if (!i.length) return !0;
		let o = Bt(i, a), s = new Wt(i, o, 0).goto(n), c = new Wt(a, o, 0).goto(n);
		for (;;) {
			if (s.to != c.to || !Kt(s.active, c.active) || s.point && (!c.point || !Pt(s.point, c.point))) return !1;
			if (s.to > r) return !0;
			s.next(), c.next();
		}
	}
	static spans(e, t, n, r, i = -1) {
		let a = new Wt(e, null, i).goto(t), o = t, s = a.openStart;
		for (;;) {
			let e = Math.min(a.to, n);
			if (a.point) {
				let n = a.activeForPoint(a.to), i = a.pointFrom < t ? n.length + 1 : a.point.startSide < 0 ? n.length : Math.min(n.length, s);
				r.point(o, e, a.point, n, i, a.pointRank), s = Math.min(a.openEnd(e), n.length);
			} else e > o && (r.span(o, e, a.active, s), s = a.openEnd(e));
			if (a.to > n) return s + (a.point && a.to > n ? 1 : 0);
			o = a.to, a.next();
		}
	}
	static of(e, t = !1) {
		let n = new zt();
		for (let r of e instanceof Ft ? [e] : t ? Rt(e) : e) n.add(r.from, r.to, r.value);
		return n.finish();
	}
	static join(t) {
		if (!t.length) return e.empty;
		let n = t[t.length - 1];
		for (let r = t.length - 2; r >= 0; r--) for (let i = t[r]; i != e.empty; i = i.nextLayer) n = new e(i.chunkPos, i.chunk, n, Math.max(i.maxPoint, n.maxPoint));
		return n;
	}
};
P.empty = /*@__PURE__*/ new P([], [], null, -1);
function Rt(e) {
	if (e.length > 1) for (let t = e[0], n = 1; n < e.length; n++) {
		let r = e[n];
		if (It(t, r) > 0) return e.slice().sort(It);
		t = r;
	}
	return e;
}
P.empty.nextLayer = P.empty;
var zt = class e {
	finishChunk(e) {
		this.chunks.push(new Lt(this.from, this.to, this.value, this.maxPoint)), this.chunkPos.push(this.chunkStart), this.chunkStart = -1, this.setMaxPoint = Math.max(this.setMaxPoint, this.maxPoint), this.maxPoint = -1, e && (this.from = [], this.to = [], this.value = []);
	}
	constructor() {
		this.chunks = [], this.chunkPos = [], this.chunkStart = -1, this.last = null, this.lastFrom = -1e9, this.lastTo = -1e9, this.from = [], this.to = [], this.value = [], this.maxPoint = -1, this.setMaxPoint = -1, this.nextLayer = null;
	}
	add(t, n, r) {
		this.addInner(t, n, r) || (this.nextLayer || (this.nextLayer = new e())).add(t, n, r);
	}
	addInner(e, t, n) {
		let r = e - this.lastTo || n.startSide - this.last.endSide;
		if (r <= 0 && (e - this.lastFrom || n.startSide - this.last.startSide) < 0) throw Error("Ranges must be added sorted by `from` position and `startSide`");
		return r < 0 ? !1 : (this.from.length == 250 && this.finishChunk(!0), this.chunkStart < 0 && (this.chunkStart = e), this.from.push(e - this.chunkStart), this.to.push(t - this.chunkStart), this.last = n, this.lastFrom = e, this.lastTo = t, this.value.push(n), n.point && (this.maxPoint = Math.max(this.maxPoint, t - e)), !0);
	}
	addChunk(e, t) {
		if ((e - this.lastTo || t.value[0].startSide - this.last.endSide) < 0) return !1;
		this.from.length && this.finishChunk(!0), this.setMaxPoint = Math.max(this.setMaxPoint, t.maxPoint), this.chunks.push(t), this.chunkPos.push(e);
		let n = t.value.length - 1;
		return this.last = t.value[n], this.lastFrom = t.from[n] + e, this.lastTo = t.to[n] + e, !0;
	}
	finish() {
		return this.finishInner(P.empty);
	}
	finishInner(e) {
		if (this.from.length && this.finishChunk(!1), this.chunks.length == 0) return e;
		let t = P.create(this.chunkPos, this.chunks, this.nextLayer ? this.nextLayer.finishInner(e) : e, this.setMaxPoint);
		return this.from = null, t;
	}
};
function Bt(e, t, n) {
	let r = /* @__PURE__ */ new Map();
	for (let t of e) for (let e = 0; e < t.chunk.length; e++) t.chunk[e].maxPoint <= 0 && r.set(t.chunk[e], t.chunkPos[e]);
	let i = /* @__PURE__ */ new Set();
	for (let e of t) for (let t = 0; t < e.chunk.length; t++) {
		let a = r.get(e.chunk[t]);
		a != null && (n ? n.mapPos(a) : a) == e.chunkPos[t] && !(n != null && n.touchesRange(a, a + e.chunk[t].length)) && i.add(e.chunk[t]);
	}
	return i;
}
var Vt = class {
	constructor(e, t, n, r = 0) {
		this.layer = e, this.skip = t, this.minPoint = n, this.rank = r;
	}
	get startSide() {
		return this.value ? this.value.startSide : 0;
	}
	get endSide() {
		return this.value ? this.value.endSide : 0;
	}
	goto(e, t = -1e9) {
		return this.chunkIndex = this.rangeIndex = 0, this.gotoInner(e, t, !1), this;
	}
	gotoInner(e, t, n) {
		for (; this.chunkIndex < this.layer.chunk.length;) {
			let t = this.layer.chunk[this.chunkIndex];
			if (!(this.skip && this.skip.has(t) || this.layer.chunkEnd(this.chunkIndex) < e || t.maxPoint < this.minPoint)) break;
			this.chunkIndex++, n = !1;
		}
		if (this.chunkIndex < this.layer.chunk.length) {
			let r = this.layer.chunk[this.chunkIndex].findIndex(e - this.layer.chunkPos[this.chunkIndex], t, !0);
			(!n || this.rangeIndex < r) && this.setRangeIndex(r);
		}
		this.next();
	}
	forward(e, t) {
		(this.to - e || this.endSide - t) < 0 && this.gotoInner(e, t, !0);
	}
	next() {
		for (;;) if (this.chunkIndex == this.layer.chunk.length) {
			this.from = this.to = 1e9, this.value = null;
			break;
		} else {
			let e = this.layer.chunkPos[this.chunkIndex], t = this.layer.chunk[this.chunkIndex], n = e + t.from[this.rangeIndex];
			if (this.from = n, this.to = e + t.to[this.rangeIndex], this.value = t.value[this.rangeIndex], this.setRangeIndex(this.rangeIndex + 1), this.minPoint < 0 || this.value.point && this.to - this.from >= this.minPoint) break;
		}
	}
	setRangeIndex(e) {
		if (e == this.layer.chunk[this.chunkIndex].value.length) {
			if (this.chunkIndex++, this.skip) for (; this.chunkIndex < this.layer.chunk.length && this.skip.has(this.layer.chunk[this.chunkIndex]);) this.chunkIndex++;
			this.rangeIndex = 0;
		} else this.rangeIndex = e;
	}
	nextChunk() {
		this.chunkIndex++, this.rangeIndex = 0, this.next();
	}
	compare(e) {
		return this.from - e.from || this.startSide - e.startSide || this.rank - e.rank || this.to - e.to || this.endSide - e.endSide;
	}
}, Ht = class e {
	constructor(e) {
		this.heap = e;
	}
	static from(t, n = null, r = -1) {
		let i = [];
		for (let e = 0; e < t.length; e++) for (let a = t[e]; !a.isEmpty; a = a.nextLayer) a.maxPoint >= r && i.push(new Vt(a, n, r, e));
		return i.length == 1 ? i[0] : new e(i);
	}
	get startSide() {
		return this.value ? this.value.startSide : 0;
	}
	goto(e, t = -1e9) {
		for (let n of this.heap) n.goto(e, t);
		for (let e = this.heap.length >> 1; e >= 0; e--) Ut(this.heap, e);
		return this.next(), this;
	}
	forward(e, t) {
		for (let n of this.heap) n.forward(e, t);
		for (let e = this.heap.length >> 1; e >= 0; e--) Ut(this.heap, e);
		(this.to - e || this.value.endSide - t) < 0 && this.next();
	}
	next() {
		if (this.heap.length == 0) this.from = this.to = 1e9, this.value = null, this.rank = -1;
		else {
			let e = this.heap[0];
			this.from = e.from, this.to = e.to, this.value = e.value, this.rank = e.rank, e.value && e.next(), Ut(this.heap, 0);
		}
	}
};
function Ut(e, t) {
	for (let n = e[t];;) {
		let r = (t << 1) + 1;
		if (r >= e.length) break;
		let i = e[r];
		if (r + 1 < e.length && i.compare(e[r + 1]) >= 0 && (i = e[r + 1], r++), n.compare(i) < 0) break;
		e[r] = n, e[t] = i, t = r;
	}
}
var Wt = class {
	constructor(e, t, n) {
		this.minPoint = n, this.active = [], this.activeTo = [], this.activeRank = [], this.minActive = -1, this.point = null, this.pointFrom = 0, this.pointRank = 0, this.to = -1e9, this.endSide = 0, this.openStart = -1, this.cursor = Ht.from(e, t, n);
	}
	goto(e, t = -1e9) {
		return this.cursor.goto(e, t), this.active.length = this.activeTo.length = this.activeRank.length = 0, this.minActive = -1, this.to = e, this.endSide = t, this.openStart = -1, this.next(), this;
	}
	forward(e, t) {
		for (; this.minActive > -1 && (this.activeTo[this.minActive] - e || this.active[this.minActive].endSide - t) < 0;) this.removeActive(this.minActive);
		this.cursor.forward(e, t);
	}
	removeActive(e) {
		qt(this.active, e), qt(this.activeTo, e), qt(this.activeRank, e), this.minActive = Yt(this.active, this.activeTo);
	}
	addActive(e) {
		let t = 0, { value: n, to: r, rank: i } = this.cursor;
		for (; t < this.activeRank.length && (i - this.activeRank[t] || r - this.activeTo[t]) > 0;) t++;
		Jt(this.active, t, n), Jt(this.activeTo, t, r), Jt(this.activeRank, t, i), e && Jt(e, t, this.cursor.from), this.minActive = Yt(this.active, this.activeTo);
	}
	next() {
		let e = this.to, t = this.point;
		this.point = null;
		let n = this.openStart < 0 ? [] : null;
		for (;;) {
			let r = this.minActive;
			if (r > -1 && (this.activeTo[r] - this.cursor.from || this.active[r].endSide - this.cursor.startSide) < 0) {
				if (this.activeTo[r] > e) {
					this.to = this.activeTo[r], this.endSide = this.active[r].endSide;
					break;
				}
				this.removeActive(r), n && qt(n, r);
			} else if (!this.cursor.value) {
				this.to = this.endSide = 1e9;
				break;
			} else if (this.cursor.from > e) {
				this.to = this.cursor.from, this.endSide = this.cursor.startSide;
				break;
			} else {
				let e = this.cursor.value;
				if (!e.point) this.addActive(n), this.cursor.next();
				else if (t && this.cursor.to == this.to && this.cursor.from < this.cursor.to) this.cursor.next();
				else {
					this.point = e, this.pointFrom = this.cursor.from, this.pointRank = this.cursor.rank, this.to = this.cursor.to, this.endSide = e.endSide, this.cursor.next(), this.forward(this.to, this.endSide);
					break;
				}
			}
		}
		if (n) {
			this.openStart = 0;
			for (let t = n.length - 1; t >= 0 && n[t] < e; t--) this.openStart++;
		}
	}
	activeForPoint(e) {
		if (!this.active.length) return this.active;
		let t = [];
		for (let n = this.active.length - 1; n >= 0 && !(this.activeRank[n] < this.pointRank); n--) (this.activeTo[n] > e || this.activeTo[n] == e && this.active[n].endSide >= this.point.endSide) && t.push(this.active[n]);
		return t.reverse();
	}
	openEnd(e) {
		let t = 0;
		for (let n = this.activeTo.length - 1; n >= 0 && this.activeTo[n] > e; n--) t++;
		return t;
	}
};
function Gt(e, t, n, r, i, a) {
	e.goto(t), n.goto(r);
	let o = r + i, s = r, c = r - t, l = !!a.boundChange;
	for (let t = !1;;) {
		let r = e.to + c - n.to, i = r || e.endSide - n.endSide, u = i < 0 ? e.to + c : n.to, d = Math.min(u, o);
		if (e.point || n.point ? (e.point && n.point && Pt(e.point, n.point) && Kt(e.activeForPoint(e.to), n.activeForPoint(n.to)) || a.comparePoint(s, d, e.point, n.point), t = !1) : (t && a.boundChange(s), d > s && !Kt(e.active, n.active) && a.compareRange(s, d, e.active, n.active), l && d < o && (r || e.openEnd(u) != n.openEnd(u)) && (t = !0)), u > o) break;
		s = u, i <= 0 && e.next(), i >= 0 && n.next();
	}
}
function Kt(e, t) {
	if (e.length != t.length) return !1;
	for (let n = 0; n < e.length; n++) if (e[n] != t[n] && !Pt(e[n], t[n])) return !1;
	return !0;
}
function qt(e, t) {
	for (let n = t, r = e.length - 1; n < r; n++) e[n] = e[n + 1];
	e.pop();
}
function Jt(e, t, n) {
	for (let n = e.length - 1; n >= t; n--) e[n + 1] = e[n];
	e[t] = n;
}
function Yt(e, t) {
	let n = -1, r = 1e9;
	for (let i = 0; i < t.length; i++) (t[i] - r || e[i].endSide - e[n].endSide) < 0 && (n = i, r = t[i]);
	return n;
}
function Xt(e, t, n = e.length) {
	let r = 0;
	for (let i = 0; i < n && i < e.length;) e.charCodeAt(i) == 9 ? (r += t - r % t, i++) : (r++, i = w(e, i));
	return r;
}
function Zt(e, t, n, r) {
	for (let r = 0, i = 0;;) {
		if (i >= t) return r;
		if (r == e.length) break;
		i += e.charCodeAt(r) == 9 ? n - i % n : 1, r = w(e, r);
	}
	return r === !0 ? -1 : e.length;
}
for (var Qt = "ͼ", $t = typeof Symbol > "u" ? "__ͼ" : Symbol.for(Qt), en = typeof Symbol > "u" ? "__styleSet" + Math.floor(Math.random() * 1e8) : Symbol("styleSet"), tn = typeof globalThis < "u" ? globalThis : typeof window < "u" ? window : {}, nn = class {
	constructor(e, t) {
		this.rules = [];
		let { finish: n } = t || {};
		function r(e) {
			return /^@/.test(e) ? [e] : e.split(/,\s*/);
		}
		function i(e, t, a, o) {
			let s = [], c = /^@(\w+)\b/.exec(e[0]), l = c && c[1] == "keyframes";
			if (c && t == null) return a.push(e[0] + ";");
			for (let n in t) {
				let o = t[n];
				if (/&/.test(n)) i(n.split(/,\s*/).map((t) => e.map((e) => t.replace(/&/, e))).reduce((e, t) => e.concat(t)), o, a);
				else if (o && typeof o == "object") {
					if (!c) throw RangeError("The value of a property (" + n + ") should be a primitive value.");
					i(r(n), o, s, l);
				} else o != null && s.push(n.replace(/_.*/, "").replace(/[A-Z]/g, (e) => "-" + e.toLowerCase()) + ": " + o + ";");
			}
			(s.length || l) && a.push((n && !c && !o ? e.map(n) : e).join(", ") + " {" + s.join(" ") + "}");
		}
		for (let t in e) i(r(t), e[t], this.rules);
	}
	getRules() {
		return this.rules.join("\n");
	}
	static newName() {
		let e = tn[$t] || 1;
		return tn[$t] = e + 1, Qt + e.toString(36);
	}
	static mount(e, t, n) {
		let r = e[en], i = n && n.nonce;
		r ? i && r.setNonce(i) : r = new an(e, i), r.mount(Array.isArray(t) ? t : [t], e);
	}
}, rn = /* @__PURE__ */ new Map(), an = class {
	constructor(e, t) {
		let n = e.ownerDocument || e, r = n.defaultView;
		if (!e.head && e.adoptedStyleSheets && r.CSSStyleSheet) {
			let t = rn.get(n);
			if (t) return e[en] = t;
			this.sheet = new r.CSSStyleSheet(), rn.set(n, this);
		} else this.styleTag = n.createElement("style"), t && this.styleTag.setAttribute("nonce", t);
		this.modules = [], e[en] = this;
	}
	mount(e, t) {
		let n = this.sheet, r = 0, i = 0;
		for (let t = 0; t < e.length; t++) {
			let a = e[t], o = this.modules.indexOf(a);
			if (o < i && o > -1 && (this.modules.splice(o, 1), i--, o = -1), o == -1) {
				if (this.modules.splice(i++, 0, a), n) for (let e = 0; e < a.rules.length; e++) n.insertRule(a.rules[e], r++);
			} else {
				for (; i < o;) r += this.modules[i++].rules.length;
				r += a.rules.length, i++;
			}
		}
		if (n) t.adoptedStyleSheets.indexOf(this.sheet) < 0 && (t.adoptedStyleSheets = [this.sheet, ...t.adoptedStyleSheets]);
		else {
			let e = "";
			for (let t = 0; t < this.modules.length; t++) e += this.modules[t].getRules() + "\n";
			this.styleTag.textContent = e;
			let n = t.head || t;
			this.styleTag.parentNode != n && n.insertBefore(this.styleTag, n.firstChild);
		}
	}
	setNonce(e) {
		this.styleTag && this.styleTag.getAttribute("nonce") != e && this.styleTag.setAttribute("nonce", e);
	}
}, on = {
	8: "Backspace",
	9: "Tab",
	10: "Enter",
	12: "NumLock",
	13: "Enter",
	16: "Shift",
	17: "Control",
	18: "Alt",
	20: "CapsLock",
	27: "Escape",
	32: " ",
	33: "PageUp",
	34: "PageDown",
	35: "End",
	36: "Home",
	37: "ArrowLeft",
	38: "ArrowUp",
	39: "ArrowRight",
	40: "ArrowDown",
	44: "PrintScreen",
	45: "Insert",
	46: "Delete",
	59: ";",
	61: "=",
	91: "Meta",
	92: "Meta",
	106: "*",
	107: "+",
	108: ",",
	109: "-",
	110: ".",
	111: "/",
	144: "NumLock",
	145: "ScrollLock",
	160: "Shift",
	161: "Shift",
	162: "Control",
	163: "Control",
	164: "Alt",
	165: "Alt",
	173: "-",
	186: ";",
	187: "=",
	188: ",",
	189: "-",
	190: ".",
	191: "/",
	192: "`",
	219: "[",
	220: "\\",
	221: "]",
	222: "'"
}, sn = {
	48: ")",
	49: "!",
	50: "@",
	51: "#",
	52: "$",
	53: "%",
	54: "^",
	55: "&",
	56: "*",
	57: "(",
	59: ":",
	61: "+",
	173: "_",
	186: ":",
	187: "+",
	188: "<",
	189: "_",
	190: ">",
	191: "?",
	192: "~",
	219: "{",
	220: "|",
	221: "}",
	222: "\""
}, cn = typeof navigator < "u" && /Mac/.test(navigator.platform), ln = typeof navigator < "u" && /MSIE \d|Trident\/(?:[7-9]|\d{2,})\..*rv:(\d+)/.exec(navigator.userAgent), F = 0; F < 10; F++) on[48 + F] = on[96 + F] = String(F);
for (var F = 1; F <= 24; F++) on[F + 111] = "F" + F;
for (var F = 65; F <= 90; F++) on[F] = String.fromCharCode(F + 32), sn[F] = String.fromCharCode(F);
for (var un in on) sn.hasOwnProperty(un) || (sn[un] = on[un]);
function dn(e) {
	var t = !(cn && e.metaKey && e.shiftKey && !e.ctrlKey && !e.altKey || ln && e.shiftKey && e.key && e.key.length == 1 || e.key == "Unidentified") && e.key || (e.shiftKey ? sn : on)[e.keyCode] || e.key || "Unidentified";
	return t == "Esc" && (t = "Escape"), t == "Del" && (t = "Delete"), t == "Left" && (t = "ArrowLeft"), t == "Up" && (t = "ArrowUp"), t == "Right" && (t = "ArrowRight"), t == "Down" && (t = "ArrowDown"), t;
}
//#endregion
//#region node_modules/crelt/index.js
function I() {
	var e = arguments[0];
	typeof e == "string" && (e = document.createElement(e));
	var t = 1, n = arguments[1];
	if (n && typeof n == "object" && n.nodeType == null && !Array.isArray(n)) {
		for (var r in n) if (Object.prototype.hasOwnProperty.call(n, r)) {
			var i = n[r];
			typeof i == "string" ? e.setAttribute(r, i) : i != null && (e[r] = i);
		}
		t++;
	}
	for (; t < arguments.length; t++) fn(e, arguments[t]);
	return e;
}
function fn(e, t) {
	if (typeof t == "string") e.appendChild(document.createTextNode(t));
	else if (t != null) {
		if (t.nodeType != null) e.appendChild(t);
		else if (Array.isArray(t)) for (var n = 0; n < t.length; n++) fn(e, t[n]);
		else throw RangeError("Unsupported child node: " + t);
	}
}
//#endregion
//#region \0@oxc-project+runtime@0.147.0/helpers/esm/typeof.js
function pn(e) {
	"@babel/helpers - typeof";
	return pn = typeof Symbol == "function" && typeof Symbol.iterator == "symbol" ? function(e) {
		return typeof e;
	} : function(e) {
		return e && typeof Symbol == "function" && e.constructor === Symbol && e !== Symbol.prototype ? "symbol" : typeof e;
	}, pn(e);
}
//#endregion
//#region \0@oxc-project+runtime@0.147.0/helpers/esm/toPrimitive.js
function mn(e, t) {
	if (pn(e) != "object" || !e) return e;
	var n = e[Symbol.toPrimitive];
	if (n !== void 0) {
		var r = n.call(e, t || "default");
		if (pn(r) != "object") return r;
		throw TypeError("@@toPrimitive must return a primitive value.");
	}
	return (t === "string" ? String : Number)(e);
}
//#endregion
//#region \0@oxc-project+runtime@0.147.0/helpers/esm/toPropertyKey.js
function hn(e) {
	var t = mn(e, "string");
	return pn(t) == "symbol" ? t : t + "";
}
//#endregion
//#region \0@oxc-project+runtime@0.147.0/helpers/esm/defineProperty.js
function gn(e, t, n) {
	return (t = hn(t)) in e ? Object.defineProperty(e, t, {
		value: n,
		enumerable: !0,
		configurable: !0,
		writable: !0
	}) : e[t] = n, e;
}
//#endregion
//#region \0@oxc-project+runtime@0.147.0/helpers/esm/objectSpread2.js
function _n(e, t) {
	var n = Object.keys(e);
	if (Object.getOwnPropertySymbols) {
		var r = Object.getOwnPropertySymbols(e);
		t && (r = r.filter(function(t) {
			return Object.getOwnPropertyDescriptor(e, t).enumerable;
		})), n.push.apply(n, r);
	}
	return n;
}
function vn(e) {
	for (var t = 1; t < arguments.length; t++) {
		var n = arguments[t] == null ? {} : arguments[t];
		t % 2 ? _n(Object(n), !0).forEach(function(t) {
			gn(e, t, n[t]);
		}) : Object.getOwnPropertyDescriptors ? Object.defineProperties(e, Object.getOwnPropertyDescriptors(n)) : _n(Object(n)).forEach(function(t) {
			Object.defineProperty(e, t, Object.getOwnPropertyDescriptor(n, t));
		});
	}
	return e;
}
//#endregion
//#region node_modules/@codemirror/view/dist/index.js
var L = typeof navigator < "u" ? navigator : {
	userAgent: "",
	vendor: "",
	platform: ""
}, yn = typeof document < "u" ? document : { documentElement: { style: {} } }, bn = /*@__PURE__*/ /Edge\/(\d+)/.exec(L.userAgent), xn = /*@__PURE__*/ /MSIE \d/.test(L.userAgent), Sn = /*@__PURE__*/ /Trident\/(?:[7-9]|\d{2,})\..*rv:(\d+)/.exec(L.userAgent), Cn = !!(xn || Sn || bn), wn = !Cn && /*@__PURE__*/ /gecko\/(\d+)/i.test(L.userAgent), Tn = !Cn && /*@__PURE__*/ /Chrome\/(\d+)/.exec(L.userAgent), En = "webkitFontSmoothing" in yn.documentElement.style, Dn = !Cn && /*@__PURE__*/ /Apple Computer/.test(L.vendor), On = Dn && (/*@__PURE__*/ /Mobile\/\w+/.test(L.userAgent) || L.maxTouchPoints > 2), R = {
	mac: On || /*@__PURE__*/ /Mac/.test(L.platform),
	windows: /*@__PURE__*/ /Win/.test(L.platform),
	linux: /*@__PURE__*/ /Linux|X11/.test(L.platform),
	ie: Cn,
	ie_version: xn ? yn.documentMode || 6 : Sn ? +Sn[1] : bn ? +bn[1] : 0,
	gecko: wn,
	gecko_version: wn ? +(/*@__PURE__*/ /Firefox\/(\d+)/.exec(L.userAgent) || [0, 0])[1] : 0,
	chrome: !!Tn,
	chrome_version: Tn ? +Tn[1] : 0,
	ios: On,
	android: /*@__PURE__*/ /Android\b/.test(L.userAgent),
	webkit: En,
	webkit_version: En ? +(/*@__PURE__*/ /\bAppleWebKit\/(\d+)/.exec(L.userAgent) || [0, 0])[1] : 0,
	safari: Dn,
	safari_version: Dn ? +(/*@__PURE__*/ /\bVersion\/(\d+(\.\d+)?)/.exec(L.userAgent) || [0, 0])[1] : 0,
	tabSize: yn.documentElement.style.tabSize == null ? "-moz-tab-size" : "tab-size"
};
function kn(e, t) {
	for (let n in e) n == "class" && t.class ? t.class += " " + e.class : n == "style" && t.style ? t.style += ";" + e.style : t[n] = e[n];
	return t;
}
var An = /*@__PURE__*/ Object.create(null);
function jn(e, t, n) {
	if (e == t) return !0;
	e || (e = An), t || (t = An);
	let r = Object.keys(e), i = Object.keys(t);
	if (r.length - (n && r.indexOf(n) > -1 ? 1 : 0) != i.length - (n && i.indexOf(n) > -1 ? 1 : 0)) return !1;
	for (let a of r) if (a != n && (i.indexOf(a) == -1 || e[a] !== t[a])) return !1;
	return !0;
}
function Mn(e, t) {
	for (let n = e.attributes.length - 1; n >= 0; n--) {
		let r = e.attributes[n].name;
		t[r] == null && e.removeAttribute(r);
	}
	for (let n in t) {
		let r = t[n];
		n == "style" ? e.style.cssText = r : e.getAttribute(n) != r && e.setAttribute(n, r);
	}
}
function Nn(e, t, n) {
	let r = !1;
	if (t) for (let i in t) n && i in n || (r = !0, i == "style" ? e.style.cssText = "" : e.removeAttribute(i));
	if (n) for (let i in n) t && t[i] == n[i] || (r = !0, i == "style" ? e.style.cssText = n[i] : e.setAttribute(i, n[i]));
	return r;
}
function Pn(e) {
	let t = Object.create(null);
	for (let n = 0; n < e.attributes.length; n++) {
		let r = e.attributes[n];
		t[r.name] = r.value;
	}
	return t;
}
var Fn = class {
	eq(e) {
		return !1;
	}
	updateDOM(e, t, n) {
		return !1;
	}
	compare(e) {
		return this == e || this.constructor == e.constructor && this.eq(e);
	}
	get estimatedHeight() {
		return -1;
	}
	get lineBreaks() {
		return 0;
	}
	ignoreEvent(e) {
		return !0;
	}
	coordsAt(e, t, n) {
		return null;
	}
	get isHidden() {
		return !1;
	}
	get editable() {
		return !1;
	}
	destroy(e) {}
}, z = /*@__PURE__*/ (function(e) {
	return e[e.Text = 0] = "Text", e[e.WidgetBefore = 1] = "WidgetBefore", e[e.WidgetAfter = 2] = "WidgetAfter", e[e.WidgetRange = 3] = "WidgetRange", e;
})(z || (z = {})), B = class extends Nt {
	constructor(e, t, n, r) {
		super(), this.startSide = e, this.endSide = t, this.widget = n, this.spec = r;
	}
	get heightRelevant() {
		return !1;
	}
	static mark(e) {
		return new In(e);
	}
	static widget(e) {
		let t = Math.max(-1e4, Math.min(1e4, e.side || 0)), n = !!e.block;
		return t += n && !e.inlineOrder ? t > 0 ? 3e8 : -4e8 : t > 0 ? 1e8 : -1e8, new Rn(e, t, t, n, e.widget || null, !1);
	}
	static replace(e) {
		let t = !!e.block, n, r;
		if (e.isBlockGap) n = -5e8, r = 4e8;
		else {
			let { start: i, end: a } = zn(e, t);
			n = (i ? t ? -3e8 : -1 : 5e8) - 1, r = (a ? t ? 2e8 : 1 : -6e8) + 1;
		}
		return new Rn(e, n, r, t, e.widget || null, !0);
	}
	static line(e) {
		return new Ln(e);
	}
	static set(e, t = !1) {
		return P.of(e, t);
	}
	hasHeight() {
		return this.widget ? this.widget.estimatedHeight > -1 : !1;
	}
};
B.none = P.empty;
var In = class e extends B {
	constructor(e) {
		let { start: t, end: n } = zn(e);
		super(t ? -1 : 5e8, n ? 1 : -6e8, null, e), this.tagName = e.tagName || "span", this.attrs = e.class && e.attributes ? kn(e.attributes, { class: e.class }) : e.class ? { class: e.class } : e.attributes || An;
	}
	eq(t) {
		return this == t || t instanceof e && this.tagName == t.tagName && jn(this.attrs, t.attrs);
	}
	range(e, t = e) {
		if (e >= t) throw RangeError("Mark decorations may not be empty");
		return super.range(e, t);
	}
};
In.prototype.point = !1;
var Ln = class e extends B {
	constructor(e) {
		super(-2e8, -2e8, null, e);
	}
	eq(t) {
		return t instanceof e && this.spec.class == t.spec.class && jn(this.spec.attributes, t.spec.attributes);
	}
	range(e, t = e) {
		if (t != e) throw RangeError("Line decoration ranges must be zero-length");
		return super.range(e, t);
	}
};
Ln.prototype.mapMode = T.TrackBefore, Ln.prototype.point = !0;
var Rn = class e extends B {
	constructor(e, t, n, r, i, a) {
		super(t, n, i, e), this.block = r, this.isReplace = a, this.mapMode = r ? t <= 0 ? T.TrackBefore : T.TrackAfter : T.TrackDel;
	}
	get type() {
		return this.startSide == this.endSide ? this.startSide <= 0 ? z.WidgetBefore : z.WidgetAfter : z.WidgetRange;
	}
	get heightRelevant() {
		return this.block || !!this.widget && (this.widget.estimatedHeight >= 5 || this.widget.lineBreaks > 0);
	}
	eq(t) {
		return t instanceof e && Bn(this.widget, t.widget) && this.block == t.block && this.startSide == t.startSide && this.endSide == t.endSide;
	}
	range(e, t = e) {
		if (this.isReplace && (e > t || e == t && this.startSide > 0 && this.endSide <= 0)) throw RangeError("Invalid range for replacement decoration");
		if (!this.isReplace && t != e) throw RangeError("Widget decorations can only have zero-length ranges");
		return super.range(e, t);
	}
};
Rn.prototype.point = !0;
function zn(e, t = !1) {
	let { inclusiveStart: n, inclusiveEnd: r } = e;
	return n == null && (n = e.inclusive), r == null && (r = e.inclusive), {
		start: n == null ? t : n,
		end: r == null ? t : r
	};
}
function Bn(e, t) {
	return e == t || !!(e && t && e.compare(t));
}
function Vn(e, t, n, r = 0) {
	let i = n.length - 1;
	i >= 0 && n[i] + r >= e ? n[i] = Math.max(n[i], t) : n.push(e, t);
}
var Hn = class e extends Nt {
	constructor(e, t, n) {
		super(), this.tagName = e, this.attributes = t, this.rank = n;
	}
	eq(t) {
		return t == this || t instanceof e && this.tagName == t.tagName && jn(this.attributes, t.attributes);
	}
	static create(t) {
		return new e(t.tagName, t.attributes || An, t.rank == null ? 50 : Math.max(0, Math.min(t.rank, 100)));
	}
	static set(e, t = !1) {
		return P.of(e, t);
	}
};
Hn.prototype.startSide = Hn.prototype.endSide = -1;
function Un(e) {
	let t;
	return t = e.nodeType == 11 ? e.getSelection ? e : e.ownerDocument : e, t.getSelection();
}
function Wn(e, t) {
	return t ? e == t || e.contains(t.nodeType == 1 ? t : t.parentNode) : !1;
}
function Gn(e, t) {
	if (!t.anchorNode) return !1;
	try {
		return Wn(e, t.anchorNode);
	} catch (e) {
		return !1;
	}
}
function Kn(e) {
	return e.nodeType == 3 ? lr(e, 0, e.nodeValue.length).getClientRects() : e.nodeType == 1 ? e.getClientRects() : [];
}
function qn(e, t, n, r) {
	return n ? Xn(e, t, n, r, -1) || Xn(e, t, n, r, 1) : !1;
}
function Jn(e) {
	for (var t = 0;; t++) if (e = e.previousSibling, !e) return t;
}
function Yn(e) {
	return e.nodeType == 1 && /^(DIV|P|LI|UL|OL|BLOCKQUOTE|DD|DT|H\d|SECTION|PRE)$/.test(e.nodeName);
}
function Xn(e, t, n, r, i) {
	for (;;) {
		if (e == n && t == r) return !0;
		if (t == (i < 0 ? 0 : Zn(e))) {
			if (e.nodeName == "DIV") return !1;
			let n = e.parentNode;
			if (!n || n.nodeType != 1) return !1;
			t = Jn(e) + (i < 0 ? 0 : 1), e = n;
		} else if (e.nodeType == 1) {
			if (e = e.childNodes[t + (i < 0 ? -1 : 0)], e.nodeType == 1 && e.contentEditable == "false") return !1;
			t = i < 0 ? Zn(e) : 0;
		} else return !1;
	}
}
function Zn(e) {
	return e.nodeType == 3 ? e.nodeValue.length : e.childNodes.length;
}
function Qn(e, t) {
	let { left: n, right: r } = e;
	if (n == r) return e;
	let i = t ? n : r;
	return {
		left: i,
		right: i,
		top: e.top,
		bottom: e.bottom
	};
}
function $n(e) {
	let t = e.visualViewport;
	return t ? {
		left: 0,
		right: t.width,
		top: 0,
		bottom: t.height
	} : {
		left: 0,
		right: e.innerWidth,
		top: 0,
		bottom: e.innerHeight
	};
}
function er(e, t) {
	let n = t.width / e.offsetWidth, r = t.height / e.offsetHeight;
	return (n > .995 && n < 1.005 || !isFinite(n) || Math.abs(t.width - e.offsetWidth) < 1) && (n = 1), (r > .995 && r < 1.005 || !isFinite(r) || Math.abs(t.height - e.offsetHeight) < 1) && (r = 1), {
		scaleX: n,
		scaleY: r
	};
}
function tr(e, t, n, r, i, a, o, s) {
	let c = e.ownerDocument, l = c.defaultView || window;
	for (let u = e, d = !1; u && !d;) if (u.nodeType == 1) {
		let e, f = u == c.body, p = 1, m = 1;
		if (f) e = $n(l);
		else {
			if (/^(fixed|sticky)$/.test(getComputedStyle(u).position) && (d = !0), u.scrollHeight <= u.clientHeight && u.scrollWidth <= u.clientWidth) {
				u = u.assignedSlot || u.parentNode;
				continue;
			}
			let t = u.getBoundingClientRect();
			({scaleX: p, scaleY: m} = er(u, t)), e = {
				left: t.left,
				right: t.left + u.clientWidth * p,
				top: t.top,
				bottom: t.top + u.clientHeight * m
			};
		}
		let h = 0, g = 0;
		if (i == "nearest") t.top < e.top + o ? (g = t.top - (e.top + o), n > 0 && t.bottom > e.bottom + g && (g = t.bottom - e.bottom + o)) : t.bottom > e.bottom - o && (g = t.bottom - e.bottom + o, n < 0 && t.top - g < e.top && (g = t.top - (e.top + o)));
		else {
			let r = t.bottom - t.top, a = e.bottom - e.top;
			g = (i == "center" && r <= a ? t.top + r / 2 - a / 2 : i == "start" || i == "center" && n < 0 ? t.top - o : t.bottom - a + o) - e.top;
		}
		if (r == "nearest" ? t.left < e.left + a ? (h = t.left - (e.left + a), n > 0 && t.right > e.right + h && (h = t.right - e.right + a)) : t.right > e.right - a && (h = t.right - e.right + a, n < 0 && t.left < e.left + h && (h = t.left - (e.left + a))) : h = (r == "center" ? t.left + (t.right - t.left) / 2 - (e.right - e.left) / 2 : r == "start" == s ? t.left - a : t.right - (e.right - e.left) + a) - e.left, h || g) {
			if (f) l.scrollBy(h, g);
			else {
				let e = 0, n = 0;
				if (g) {
					let e = u.scrollTop;
					u.scrollTop += g / m, n = (u.scrollTop - e) * m;
				}
				if (h) {
					let t = u.scrollLeft;
					u.scrollLeft += h / p, e = (u.scrollLeft - t) * p;
				}
				t = {
					left: t.left - e,
					top: t.top - n,
					right: t.right - e,
					bottom: t.bottom - n
				}, e && Math.abs(e - h) < 1 && (r = "nearest"), n && Math.abs(n - g) < 1 && (i = "nearest");
			}
		}
		if (f) break;
		(t.top < e.top || t.bottom > e.bottom || t.left < e.left || t.right > e.right) && (t = {
			left: Math.max(t.left, e.left),
			right: Math.min(t.right, e.right),
			top: Math.max(t.top, e.top),
			bottom: Math.min(t.bottom, e.bottom)
		}), u = u.assignedSlot || u.parentNode;
	} else if (u.nodeType == 11) u = u.host;
	else break;
}
function nr(e, t = !0) {
	let n = e.ownerDocument, r = null, i = null;
	for (let a = e.parentNode; a && !(a == n.body || (!t || r) && i);) if (a.nodeType == 1) !i && a.scrollHeight > a.clientHeight && (i = a), t && !r && a.scrollWidth > a.clientWidth && (r = a), a = a.assignedSlot || a.parentNode;
	else if (a.nodeType == 11) a = a.host;
	else break;
	return {
		x: r,
		y: i
	};
}
var rr = class {
	constructor() {
		this.anchorNode = null, this.anchorOffset = 0, this.focusNode = null, this.focusOffset = 0;
	}
	eq(e) {
		return this.anchorNode == e.anchorNode && this.anchorOffset == e.anchorOffset && this.focusNode == e.focusNode && this.focusOffset == e.focusOffset;
	}
	setRange(e) {
		let { anchorNode: t, focusNode: n } = e;
		this.set(t, Math.min(e.anchorOffset, t ? Zn(t) : 0), n, Math.min(e.focusOffset, n ? Zn(n) : 0));
	}
	set(e, t, n, r) {
		this.anchorNode = e, this.anchorOffset = t, this.focusNode = n, this.focusOffset = r;
	}
};
function ir(e) {
	let t = [];
	for (let n = e; n; n = n.nodeType == 11 ? n.host : n.parentNode) n.nodeType == 1 && t.push({
		node: n,
		left: n.scrollLeft,
		top: n.scrollTop
	});
	return t;
}
function ar(e, t = !0) {
	for (let { node: n, left: r, top: i } of e) t && n.scrollTop != i && (n.scrollTop = i), n.scrollLeft != r && (n.scrollLeft = r);
}
var or = null;
R.safari && R.safari_version >= 26 && (or = !1);
function sr(e) {
	if (e.setActive) return e.setActive();
	if (or) return e.focus(or);
	let t = ir(e);
	e.focus(or == null ? { get preventScroll() {
		return or = { preventScroll: !0 }, !0;
	} } : void 0), or || (or = !1, ar(t));
}
var cr;
function lr(e, t, n = t) {
	let r = cr || (cr = document.createRange());
	return r.setEnd(e, n), r.setStart(e, t), r;
}
function ur(e, t, n, r) {
	let i = {
		key: t,
		code: t,
		keyCode: n,
		which: n,
		cancelable: !0
	};
	r && ({altKey: i.altKey, ctrlKey: i.ctrlKey, shiftKey: i.shiftKey, metaKey: i.metaKey} = r);
	let a = new KeyboardEvent("keydown", i);
	a.synthetic = !0, e.dispatchEvent(a);
	let o = new KeyboardEvent("keyup", i);
	return o.synthetic = !0, e.dispatchEvent(o), a.defaultPrevented || o.defaultPrevented;
}
function dr(e) {
	for (; e;) {
		if (e && (e.nodeType == 9 || e.nodeType == 11 && e.host)) return e;
		e = e.assignedSlot || e.parentNode;
	}
	return null;
}
function fr(e, t) {
	let n = t.focusNode, r = t.focusOffset;
	if (!n || t.anchorNode != n || t.anchorOffset != r) return !1;
	for (r = Math.min(r, Zn(n));;) if (r) {
		if (n.nodeType != 1) return !1;
		let e = n.childNodes[r - 1];
		e.contentEditable == "false" ? r-- : (n = e, r = Zn(n));
	} else if (n == e) return !0;
	else r = Jn(n), n = n.parentNode;
}
function pr(e) {
	return e instanceof Window ? e.pageYOffset > Math.max(0, e.document.documentElement.scrollHeight - e.innerHeight - 4) : e.scrollTop > Math.max(1, e.scrollHeight - e.clientHeight - 4);
}
function mr(e, t) {
	for (let n = e, r = t;;) if (n.nodeType == 3 && r > 0) return {
		node: n,
		offset: r
	};
	else if (n.nodeType == 1 && r > 0) {
		if (n.contentEditable == "false") return null;
		n = n.childNodes[r - 1], r = Zn(n);
	} else if (n.parentNode && !Yn(n)) r = Jn(n), n = n.parentNode;
	else return null;
}
function hr(e, t) {
	for (let n = e, r = t;;) if (n.nodeType == 3 && r < n.nodeValue.length) return {
		node: n,
		offset: r
	};
	else if (n.nodeType == 1 && r < n.childNodes.length) {
		if (n.contentEditable == "false") return null;
		n = n.childNodes[r], r = 0;
	} else if (n.parentNode && !Yn(n)) r = Jn(n) + 1, n = n.parentNode;
	else return null;
}
var gr = class e {
	constructor(e, t, n = !0) {
		this.node = e, this.offset = t, this.precise = n;
	}
	static before(t, n) {
		return new e(t.parentNode, Jn(t), n);
	}
	static after(t, n) {
		return new e(t.parentNode, Jn(t) + 1, n);
	}
}, V = /*@__PURE__*/ (function(e) {
	return e[e.LTR = 0] = "LTR", e[e.RTL = 1] = "RTL", e;
})(V || (V = {})), _r = V.LTR, vr = V.RTL;
function yr(e) {
	let t = [];
	for (let n = 0; n < e.length; n++) t.push(1 << e[n]);
	return t;
}
var br = /*@__PURE__*/ yr("88888888888888888888888888888888888666888888787833333333337888888000000000000000000000000008888880000000000000000000000000088888888888888888888888888888888888887866668888088888663380888308888800000000000000000000000800000000000000000000000000000008"), xr = /*@__PURE__*/ yr("4444448826627288999999999992222222222222222222222222222222222222222222222229999999999999999999994444444444644222822222222222222222222222222222222222222222222222222222222222222222222222222222222222222222222222222222999999949999999229989999223333333333"), Sr = /*@__PURE__*/ Object.create(null), Cr = [];
for (let e of [
	"()",
	"[]",
	"{}"
]) {
	let t = /*@__PURE__*/ e.charCodeAt(0), n = /*@__PURE__*/ e.charCodeAt(1);
	Sr[t] = n, Sr[n] = -t;
}
function wr(e) {
	return e <= 247 ? br[e] : 1424 <= e && e <= 1524 ? 2 : 1536 <= e && e <= 1785 ? xr[e - 1536] : 1774 <= e && e <= 2220 ? 4 : 8192 <= e && e <= 8204 ? 256 : 64336 <= e && e <= 65023 ? 4 : 1;
}
var Tr = /[\u0590-\u05f4\u0600-\u06ff\u0700-\u08ac\ufb50-\ufdff]/, Er = class {
	get dir() {
		return this.level % 2 ? vr : _r;
	}
	constructor(e, t, n) {
		this.from = e, this.to = t, this.level = n;
	}
	side(e, t) {
		return this.dir == t == e ? this.to : this.from;
	}
	forward(e, t) {
		return e == (this.dir == t);
	}
	static find(e, t, n, r) {
		let i = -1;
		for (let a = 0; a < e.length; a++) {
			let o = e[a];
			if (o.from <= t && o.to >= t) {
				if (o.level == n) return a;
				(i < 0 || (r == 0 ? e[i].level > o.level : r < 0 ? o.from < t : o.to > t)) && (i = a);
			}
		}
		if (i < 0) throw RangeError("Index out of range");
		return i;
	}
};
function Dr(e, t) {
	if (e.length != t.length) return !1;
	for (let n = 0; n < e.length; n++) {
		let r = e[n], i = t[n];
		if (r.from != i.from || r.to != i.to || r.direction != i.direction || !Dr(r.inner, i.inner)) return !1;
	}
	return !0;
}
var H = [];
function Or(e, t, n, r, i) {
	for (let a = 0; a <= r.length; a++) {
		let o = a ? r[a - 1].to : t, s = a < r.length ? r[a].from : n, c = a ? 256 : i;
		for (let t = o, n = c, r = c; t < s; t++) {
			let i = wr(e.charCodeAt(t));
			i == 512 ? i = n : i == 8 && r == 4 && (i = 16), H[t] = i == 4 ? 2 : i, i & 7 && (r = i), n = i;
		}
		for (let e = o, t = c, r = c; e < s; e++) {
			let i = H[e];
			if (i == 128) e < s - 1 && t == H[e + 1] && t & 24 ? i = H[e] = t : H[e] = 256;
			else if (i == 64) {
				let i = e + 1;
				for (; i < s && H[i] == 64;) i++;
				let a = e && t == 8 || i < n && H[i] == 8 ? r == 1 ? 1 : 8 : 256;
				for (let t = e; t < i; t++) H[t] = a;
				e = i - 1;
			} else i == 8 && r == 1 && (H[e] = 1);
			t = i, i & 7 && (r = i);
		}
	}
}
function kr(e, t, n, r, i) {
	let a = i == 1 ? 2 : 1;
	for (let o = 0, s = 0, c = 0; o <= r.length; o++) {
		let l = o ? r[o - 1].to : t, u = o < r.length ? r[o].from : n;
		for (let t = l, n, r, o; t < u; t++) if (r = Sr[n = e.charCodeAt(t)]) {
			if (r < 0) {
				for (let e = s - 3; e >= 0; e -= 3) if (Cr[e + 1] == -r) {
					let n = Cr[e + 2], r = n & 2 ? i : n & 4 ? n & 1 ? a : i : 0;
					r && (H[t] = H[Cr[e]] = r), s = e;
					break;
				}
			} else if (Cr.length == 189) break;
			else Cr[s++] = t, Cr[s++] = n, Cr[s++] = c;
		} else if ((o = H[t]) == 2 || o == 1) {
			let e = o == i;
			c = +!e;
			for (let t = s - 3; t >= 0; t -= 3) {
				let n = Cr[t + 2];
				if (n & 2) break;
				if (e) Cr[t + 2] |= 2;
				else {
					if (n & 4) break;
					Cr[t + 2] |= 4;
				}
			}
		}
	}
}
function Ar(e, t, n, r) {
	for (let i = 0, a = r; i <= n.length; i++) {
		let o = i ? n[i - 1].to : e, s = i < n.length ? n[i].from : t;
		for (let c = o; c < s;) {
			let o = H[c];
			if (o == 256) {
				let o = c + 1;
				for (;;) if (o == s) {
					if (i == n.length) break;
					o = n[i++].to, s = i < n.length ? n[i].from : t;
				} else if (H[o] == 256) o++;
				else break;
				let l = a == 1, u = l == ((o < t ? H[o] : r) == 1) ? l ? 1 : 2 : r;
				for (let t = o, r = i, a = r ? n[r - 1].to : e; t > c;) t == a && (t = n[--r].from, a = r ? n[r - 1].to : e), H[--t] = u;
				c = o;
			} else a = o, c++;
		}
	}
}
function jr(e, t, n, r, i, a, o) {
	let s = r % 2 ? 2 : 1;
	if (r % 2 == i % 2) for (let c = t, l = 0; c < n;) {
		let t = !0, u = !1;
		if (l == a.length || c < a[l].from) {
			let e = H[c];
			e != s && (t = !1, u = e == 16);
		}
		let d = !t && s == 1 ? [] : null, f = t ? r : r + 1, p = c;
		run: for (;;) if (l < a.length && p == a[l].from) {
			if (u) break run;
			let m = a[l];
			if (!t) for (let e = m.to, t = l + 1;;) {
				if (e == n) break run;
				if (t < a.length && a[t].from == e) e = a[t++].to;
				else if (H[e] == s) break run;
				else break;
			}
			l++, d ? d.push(m) : (m.from > c && o.push(new Er(c, m.from, f)), Mr(e, m.direction == _r == !(f % 2) ? r : r + 1, i, m.inner, m.from, m.to, o), c = m.to), p = m.to;
		} else if (p == n || (t ? H[p] != s : H[p] == s)) break;
		else p++;
		d ? jr(e, c, p, r + 1, i, d, o) : c < p && o.push(new Er(c, p, f)), c = p;
	}
	else for (let c = n, l = a.length; c > t;) {
		let n = !0, u = !1;
		if (!l || c > a[l - 1].to) {
			let e = H[c - 1];
			e != s && (n = !1, u = e == 16);
		}
		let d = !n && s == 1 ? [] : null, f = n ? r : r + 1, p = c;
		run: for (;;) if (l && p == a[l - 1].to) {
			if (u) break run;
			let m = a[--l];
			if (!n) for (let e = m.from, n = l;;) {
				if (e == t) break run;
				if (n && a[n - 1].to == e) e = a[--n].from;
				else if (H[e - 1] == s) break run;
				else break;
			}
			d ? d.push(m) : (m.to < c && o.push(new Er(m.to, c, f)), Mr(e, m.direction == _r == !(f % 2) ? r : r + 1, i, m.inner, m.from, m.to, o), c = m.from), p = m.from;
		} else if (p == t || (n ? H[p - 1] != s : H[p - 1] == s)) break;
		else p--;
		d ? jr(e, p, c, r + 1, i, d, o) : p < c && o.push(new Er(p, c, f)), c = p;
	}
}
function Mr(e, t, n, r, i, a, o) {
	let s = t % 2 ? 2 : 1;
	Or(e, i, a, r, s), kr(e, i, a, r, s), Ar(i, a, r, s), jr(e, i, a, t, n, r, o);
}
function Nr(e, t, n) {
	if (!e) return [new Er(0, 0, +(t == vr))];
	if (t == _r && !n.length && !Tr.test(e)) return Pr(e.length);
	if (n.length) for (; e.length > H.length;) H[H.length] = 256;
	let r = [], i = t == _r ? 0 : 1;
	return Mr(e, i, i, n, 0, e.length, r), r;
}
function Pr(e) {
	return [new Er(0, e, 0)];
}
var Fr = "";
function Ir(e, t, n, r, i) {
	var a;
	let o = r.head - e.from, s = Er.find(t, o, (a = r.bidiLevel) == null ? -1 : a, r.assoc), c = t[s], l = c.side(i, n);
	if (o == l) {
		let e = s += i ? 1 : -1;
		if (e < 0 || e >= t.length) return null;
		c = t[s = e], o = c.side(!i, n), l = c.side(i, n);
	}
	let u = w(e.text, o, c.forward(i, n));
	(u < c.from || u > c.to) && (u = l), Fr = e.text.slice(Math.min(o, u), Math.max(o, u));
	let d = s == (i ? t.length - 1 : 0) ? null : t[s + (i ? 1 : -1)];
	return d && u == l && d.level + +!i < c.level ? D.cursor(d.side(!i, n) + e.from, d.forward(i, n) ? 1 : -1, d.level) : D.cursor(u + e.from, c.forward(i, n) ? -1 : 1, c.level);
}
function Lr(e, t, n) {
	for (let r = t; r < n; r++) {
		let t = wr(e.charCodeAt(r));
		if (t == 1) return _r;
		if (t == 2 || t == 4) return vr;
	}
	return _r;
}
var Rr = /*@__PURE__*/ O.define(), zr = /*@__PURE__*/ O.define(), Br = /*@__PURE__*/ O.define(), Vr = /*@__PURE__*/ O.define(), Hr = /*@__PURE__*/ O.define(), Ur = /*@__PURE__*/ O.define(), Wr = /*@__PURE__*/ O.define(), Gr = /*@__PURE__*/ O.define(), Kr = /*@__PURE__*/ O.define(), qr = /*@__PURE__*/ O.define({ combine: (e) => e.some((e) => e) }), Jr = /*@__PURE__*/ O.define({ combine: (e) => e.some((e) => e) }), Yr = /*@__PURE__*/ O.define(), Xr = class e {
	constructor(e, t, n, r, i, a = !1) {
		this.range = e, this.y = t, this.x = n, this.yMargin = r, this.xMargin = i, this.isSnapshot = a;
	}
	map(t) {
		return t.empty ? this : new e(this.range.map(t), this.y, this.x, this.yMargin, this.xMargin, this.isSnapshot);
	}
	clip(t) {
		return this.range.to <= t.doc.length ? this : new e(D.cursor(t.doc.length), this.y, this.x, this.yMargin, this.xMargin, this.isSnapshot);
	}
}, Zr = /*@__PURE__*/ A.define({ map: (e, t) => e.map(t) }), Qr = /*@__PURE__*/ A.define();
function U(e, t, n) {
	let r = e.facet(Vr);
	r.length ? r[0](t) : window.onerror && window.onerror(String(t), n, void 0, void 0, t) || (n ? console.error(n + ":", t) : console.error(t));
}
var $r = /*@__PURE__*/ O.define({ combine: (e) => !e.length || e[0] }), ei = 0, ti = /*@__PURE__*/ O.define({ combine(e) {
	return e.filter((t, n) => {
		for (let r = 0; r < n; r++) if (e[r].plugin == t.plugin) return !1;
		return !0;
	});
} }), W = class e {
	constructor(e, t, n, r, i) {
		this.id = e, this.create = t, this.domEventHandlers = n, this.domEventObservers = r, this.baseExtensions = i(this), this.extension = this.baseExtensions.concat(ti.of({
			plugin: this,
			arg: void 0
		}));
	}
	of(e) {
		return this.baseExtensions.concat(ti.of({
			plugin: this,
			arg: e
		}));
	}
	static define(t, n) {
		let { eventHandlers: r, eventObservers: i, provide: a, decorations: o } = n || {};
		return new e(ei++, t, r, i, (e) => {
			let t = [];
			return o && t.push(ai.of((t) => {
				let n = t.plugin(e);
				return n ? o(n) : B.none;
			})), a && t.push(a(e)), t;
		});
	}
	static fromClass(t, n) {
		return e.define((e, n) => new t(e, n), n);
	}
}, ni = class {
	constructor(e) {
		this.spec = e, this.mustUpdate = null, this.value = null;
	}
	get plugin() {
		return this.spec && this.spec.plugin;
	}
	update(e) {
		if (!this.value) {
			if (this.spec) try {
				this.value = this.spec.plugin.create(e, this.spec.arg);
			} catch (t) {
				U(e.state, t, "CodeMirror plugin crashed"), this.deactivate();
			}
		} else if (this.mustUpdate) {
			let e = this.mustUpdate;
			if (this.mustUpdate = null, this.value.update) try {
				this.value.update(e);
			} catch (t) {
				if (U(e.state, t, "CodeMirror plugin crashed"), this.value.destroy) try {
					this.value.destroy();
				} catch (e) {}
				this.deactivate();
			}
		}
		return this;
	}
	destroy(e) {
		var t;
		if ((t = this.value) != null && t.destroy) try {
			this.value.destroy();
		} catch (t) {
			U(e.state, t, "CodeMirror plugin crashed");
		}
	}
	deactivate() {
		this.spec = this.value = null;
	}
}, ri = /*@__PURE__*/ O.define(), ii = /*@__PURE__*/ O.define(), ai = /*@__PURE__*/ O.define(), oi = /*@__PURE__*/ O.define(), si = /*@__PURE__*/ O.define(), ci = /*@__PURE__*/ O.define(), li = /*@__PURE__*/ O.define();
function ui(e, t) {
	let n = e.state.facet(li);
	if (!n.length) return n;
	let r = n.map((t) => t instanceof Function ? t(e) : t), i = [];
	return P.spans(r, t.from, t.to, {
		point() {},
		span(e, n, r, a) {
			let o = e - t.from, s = n - t.from, c = i;
			for (let e = r.length - 1; e >= 0; e--, a--) {
				let n = r[e].spec.bidiIsolate, i;
				if (n == null && (n = Lr(t.text, o, s)), a > 0 && c.length && (i = c[c.length - 1]).to == o && i.direction == n) i.to = s, c = i.inner;
				else {
					let e = {
						from: o,
						to: s,
						direction: n,
						inner: []
					};
					c.push(e), c = e.inner;
				}
			}
		}
	}), i;
}
var di = /*@__PURE__*/ O.define();
function fi(e) {
	let t = 0, n = 0, r = 0, i = 0;
	for (let a of e.state.facet(di)) {
		let o = a(e);
		o && (o.left != null && (t = Math.max(t, o.left)), o.right != null && (n = Math.max(n, o.right)), o.top != null && (r = Math.max(r, o.top)), o.bottom != null && (i = Math.max(i, o.bottom)));
	}
	return {
		left: t,
		right: n,
		top: r,
		bottom: i
	};
}
var pi = /*@__PURE__*/ O.define(), mi = class e {
	constructor(e, t, n, r) {
		this.fromA = e, this.toA = t, this.fromB = n, this.toB = r;
	}
	join(t) {
		return new e(Math.min(this.fromA, t.fromA), Math.max(this.toA, t.toA), Math.min(this.fromB, t.fromB), Math.max(this.toB, t.toB));
	}
	addToSet(e) {
		let t = e.length, n = this;
		for (; t > 0; t--) {
			let r = e[t - 1];
			if (!(r.fromA > n.toA)) {
				if (r.toA < n.fromA) break;
				n = n.join(r), e.splice(t - 1, 1);
			}
		}
		return e.splice(t, 0, n), e;
	}
	static extendWithRanges(t, n) {
		if (n.length == 0) return t;
		let r = [];
		for (let i = 0, a = 0, o = 0;;) {
			let s = i < t.length ? t[i].fromB : 1e9, c = a < n.length ? n[a] : 1e9, l = Math.min(s, c);
			if (l == 1e9) break;
			let u = l + o, d = l, f = u;
			for (;;) if (a < n.length && n[a] <= d) {
				let e = n[a + 1];
				a += 2, d = Math.max(d, e);
				for (let e = i; e < t.length && t[e].fromB <= d; e++) o = t[e].toA - t[e].toB;
				f = Math.max(f, e + o);
			} else if (i < t.length && t[i].fromB <= d) {
				let e = t[i++];
				d = Math.max(d, e.toB), f = Math.max(f, e.toA), o = e.toA - e.toB;
			} else break;
			r.push(new e(u, f, l, d));
		}
		return r;
	}
}, hi = class e {
	constructor(e, t, n) {
		this.view = e, this.state = t, this.transactions = n, this.flags = 0, this.startState = e.state, this.changes = ze.empty(this.startState.doc.length);
		for (let e of n) this.changes = this.changes.compose(e.changes);
		let r = [];
		this.changes.iterChangedRanges((e, t, n, i) => r.push(new mi(e, t, n, i))), this.changedRanges = r;
	}
	static create(t, n, r) {
		return new e(t, n, r);
	}
	get viewportChanged() {
		return (this.flags & 4) > 0;
	}
	get viewportMoved() {
		return (this.flags & 8) > 0;
	}
	get heightChanged() {
		return (this.flags & 2) > 0;
	}
	get geometryChanged() {
		return this.docChanged || (this.flags & 18) > 0;
	}
	get focusChanged() {
		return (this.flags & 1) > 0;
	}
	get docChanged() {
		return !this.changes.empty;
	}
	get selectionSet() {
		return this.transactions.some((e) => e.selection);
	}
	get empty() {
		return this.flags == 0 && this.transactions.length == 0;
	}
}, gi = [], G = class {
	constructor(e, t, n = 0) {
		this.dom = e, this.length = t, this.flags = n, this.parent = null, e.cmTile = this;
	}
	get breakAfter() {
		return this.flags & 1;
	}
	get children() {
		return gi;
	}
	isWidget() {
		return !1;
	}
	get isHidden() {
		return !1;
	}
	isComposite() {
		return !1;
	}
	isLine() {
		return !1;
	}
	isText() {
		return !1;
	}
	isBlock() {
		return !1;
	}
	get domAttrs() {
		return null;
	}
	sync(e) {
		if (this.flags |= 2, this.flags & 4) {
			this.flags &= -5;
			let e = this.domAttrs;
			e && Mn(this.dom, e);
		}
	}
	toString() {
		return this.constructor.name + (this.children.length ? `(${this.children})` : "") + (this.breakAfter ? "#" : "");
	}
	destroy() {
		this.parent = null;
	}
	setDOM(e) {
		this.dom = e, e.cmTile = this;
	}
	get posAtStart() {
		return this.parent ? this.parent.posBefore(this) : 0;
	}
	get posAtEnd() {
		return this.posAtStart + this.length;
	}
	posBefore(e, t = this.posAtStart) {
		let n = t;
		for (let t of this.children) {
			if (t == e) return n;
			n += t.length + t.breakAfter;
		}
		throw RangeError("Invalid child in posBefore");
	}
	posAfter(e) {
		return this.posBefore(e) + e.length;
	}
	covers(e) {
		return !0;
	}
	coordsIn(e, t, n) {
		return null;
	}
	domPosFor(e, t) {
		let n = Jn(this.dom), r = this.length ? e > 0 : t > 0;
		return new gr(this.parent.dom, n + +!!r, e == 0 || e == this.length);
	}
	markDirty(e) {
		this.flags &= -3, e && (this.flags |= 4), this.parent && this.parent.flags & 2 && this.parent.markDirty(!1);
	}
	get overrideDOMText() {
		return null;
	}
	get root() {
		for (let e = this; e; e = e.parent) if (e instanceof yi) return e;
		return null;
	}
	static get(e) {
		return e.cmTile;
	}
}, _i = class extends G {
	constructor(e) {
		super(e, 0), this._children = [];
	}
	isComposite() {
		return !0;
	}
	get children() {
		return this._children;
	}
	get lastChild() {
		return this.children.length ? this.children[this.children.length - 1] : null;
	}
	append(e) {
		this.children.push(e), e.parent = this;
	}
	sync(e) {
		if (this.flags & 2) return;
		super.sync(e);
		let t = this.dom, n = null, r, i = (e == null ? void 0 : e.node) == t ? e : null, a = 0;
		for (let o of this.children) {
			if (o.sync(e), a += o.length + o.breakAfter, r = n ? n.nextSibling : t.firstChild, i && r != o.dom && (i.written = !0), o.dom.parentNode == t) for (; r && r != o.dom;) r = vi(r);
			else t.insertBefore(o.dom, r);
			n = o.dom;
		}
		for (r = n ? n.nextSibling : t.firstChild, i && r && (i.written = !0); r;) r = vi(r);
		this.length = a;
	}
};
function vi(e) {
	let t = e.nextSibling;
	return e.parentNode.removeChild(e), t;
}
var yi = class extends _i {
	constructor(e, t) {
		super(t), this.view = e;
	}
	owns(e) {
		for (; e; e = e.parent) if (e == this) return !0;
		return !1;
	}
	isBlock() {
		return !0;
	}
	nearest(e) {
		for (;;) {
			if (!e) return null;
			let t = G.get(e);
			if (t && this.owns(t)) return t;
			e = e.parentNode;
		}
	}
	blockTiles(e) {
		for (let t = [], n = this, r = 0, i = 0;;) if (r == n.children.length) {
			if (!t.length) return;
			n = n.parent, n.breakAfter && i++, r = t.pop();
		} else {
			let a = n.children[r++];
			if (a instanceof bi) t.push(r), n = a, r = 0;
			else {
				let t = i + a.length, n = e(a, i);
				if (n !== void 0) return n;
				i = t + a.breakAfter;
			}
		}
	}
	resolveBlock(e, t) {
		let n, r = -1, i, a = -1;
		if (this.blockTiles((o, s) => {
			let c = s + o.length;
			if (e >= s && e <= c) {
				if (o.isWidget() && t >= -1 && t <= 1) {
					if (o.flags & 32) return !0;
					o.flags & 16 && (n = void 0);
				}
				(s < e || e == c && (t < -1 ? o.length : o.covers(1))) && (!n || !o.isWidget() && n.isWidget()) && (n = o, r = e - s), (c > e || e == s && (t > 1 ? o.length : o.covers(-1))) && (!i || !o.isWidget() && i.isWidget()) && (i = o, a = e - s);
			}
		}), !n && !i) throw Error("No tile at position " + e);
		return n && t < 0 || !i ? {
			tile: n,
			offset: r
		} : {
			tile: i,
			offset: a
		};
	}
}, bi = class e extends _i {
	constructor(e, t) {
		super(e), this.wrapper = t;
	}
	isBlock() {
		return !0;
	}
	covers(e) {
		return this.children.length ? e < 0 ? this.children[0].covers(-1) : this.lastChild.covers(1) : !1;
	}
	get domAttrs() {
		return this.wrapper.attributes;
	}
	static of(t, n) {
		let r = new e(n || document.createElement(t.tagName), t);
		return n || (r.flags |= 4), r;
	}
}, xi = class e extends _i {
	constructor(e, t) {
		super(e), this.attrs = t;
	}
	isLine() {
		return !0;
	}
	static start(t, n, r) {
		let i = new e(n || document.createElement("div"), t);
		return (!n || !r) && (i.flags |= 4), i;
	}
	get domAttrs() {
		return this.attrs;
	}
	resolveInline(e, t, n) {
		let r = null, i = -1, a = null, o = -1;
		function s(e, c) {
			for (let l = 0, u = 0; l < e.children.length && u <= c; l++) {
				let d = e.children[l], f = u + d.length;
				f >= c && (d.isComposite() ? s(d, c - u) : (!a || a.isHidden && (t > 0 && !(a.flags & 32) || n && Ci(a, d))) && (f > c || d.flags & 32 && t <= 1) ? (a = d, o = c - u) : (u < c || d.flags & 16 && !d.isHidden && t >= -1) && (r = d, i = c - u)), u = f;
			}
		}
		s(this, e);
		let c = (t < 0 ? r : a) || r || a;
		return c ? {
			tile: c,
			offset: c == r ? i : o
		} : null;
	}
	coordsIn(e, t, n) {
		let r = this.resolveInline(e, t, !0);
		return r ? r.tile.coordsIn(Math.max(0, r.offset), t, n) : Si(this);
	}
	domIn(e, t) {
		let n = this.resolveInline(e, t);
		if (n) {
			let { tile: e, offset: r } = n;
			if (this.dom.contains(e.dom)) return e.isText() ? new gr(e.dom, Math.min(e.dom.nodeValue.length, r)) : e.domPosFor(r, e.flags & 16 ? 1 : e.flags & 32 ? -1 : t);
			let i = n.tile.parent, a = !1;
			for (let e of i.children) {
				if (a) return new gr(e.dom, 0);
				e == n.tile && (a = !0);
			}
		}
		return new gr(this.dom, 0);
	}
};
function Si(e) {
	let t = e.dom.lastChild;
	if (!t) return e.dom.getBoundingClientRect();
	let n = Kn(t);
	return n[n.length - 1] || null;
}
function Ci(e, t) {
	let n = e.coordsIn(0, 1), r = t.coordsIn(0, 1);
	return n && r && r.top < n.bottom;
}
var wi = class e extends _i {
	constructor(e, t) {
		super(e), this.mark = t;
	}
	get domAttrs() {
		return this.mark.attrs;
	}
	static of(t, n) {
		let r = new e(n || document.createElement(t.tagName), t);
		return n || (r.flags |= 4), r;
	}
}, Ti = class e extends G {
	constructor(e, t) {
		super(e, t.length), this.text = t;
	}
	sync(e) {
		this.flags & 2 || (super.sync(e), this.dom.nodeValue != this.text && (e && e.node == this.dom && (e.written = !0), this.dom.nodeValue = this.text));
	}
	isText() {
		return !0;
	}
	toString() {
		return JSON.stringify(this.text);
	}
	coordsIn(e, t, n) {
		let r = this.dom.nodeValue.length;
		e > r && (e = r);
		let i = e, a = e, o = 0;
		e == 0 && t < 0 || e == r && t >= 0 ? R.chrome || R.gecko || (e ? (i--, o = 1) : a < r && (a++, o = -1)) : t < 0 ? i-- : a < r && a++;
		let s = lr(this.dom, i, a).getClientRects();
		if (!s.length) return null;
		let c = s[(o ? o < 0 : t >= 0) ? 0 : s.length - 1];
		return R.safari && !o && c.width == 0 && (c = Array.prototype.find.call(s, (e) => e.width) || c), n == null ? c : Qn(c, (o ? o > 0 : t < 0) == n);
	}
	static of(t, n) {
		let r = new e(n || document.createTextNode(t), t);
		return n || (r.flags |= 2), r;
	}
}, Ei = class e extends G {
	constructor(e, t, n, r) {
		super(e, t, r), this.widget = n;
	}
	isWidget() {
		return !0;
	}
	get isHidden() {
		return this.widget.isHidden;
	}
	covers(e) {
		return this.flags & 48 ? !1 : (this.flags & (e < 0 ? 64 : 128)) > 0;
	}
	coordsIn(e, t) {
		return this.coordsInWidget(e, t, !1);
	}
	coordsInWidget(e, t, n) {
		let r = this.widget.coordsAt(this.dom, e, t);
		if (r) return r;
		if (n) return Qn(this.dom.getBoundingClientRect(), this.length ? e == 0 : t <= 0);
		{
			let t = this.dom.getClientRects(), n = null;
			if (!t.length) return null;
			let r = this.flags & 16 ? !0 : this.flags & 32 ? !1 : e > 0;
			for (let i = r ? t.length - 1 : 0; n = t[i], !(e > 0 ? i == 0 : i == t.length - 1 || n.top < n.bottom); i += r ? -1 : 1);
			return Qn(n, !r);
		}
	}
	get overrideDOMText() {
		if (!this.length) return C.empty;
		let { root: e } = this;
		if (!e) return C.empty;
		let t = this.posAtStart;
		return e.view.state.doc.slice(t, t + this.length);
	}
	destroy() {
		super.destroy(), this.widget.destroy(this.dom);
	}
	static of(t, n, r, i, a) {
		return a || (a = t.toDOM(n), t.editable || (a.contentEditable = "false")), new e(a, r, t, i);
	}
}, Di = class extends G {
	constructor(e) {
		let t = document.createElement("img");
		t.className = "cm-widgetBuffer", t.setAttribute("aria-hidden", "true"), super(t, 0, e);
	}
	get isHidden() {
		return !0;
	}
	get overrideDOMText() {
		return C.empty;
	}
	coordsIn(e, t, n) {
		let r = this.dom.getBoundingClientRect();
		return n == null ? r : Qn(r, t > 0 == n);
	}
}, Oi = class {
	constructor(e) {
		this.index = 0, this.beforeBreak = !1, this.parents = [], this.tile = e;
	}
	advance(e, t, n) {
		let { tile: r, index: i, beforeBreak: a, parents: o } = this;
		for (; e || t > 0;) if (!r.isComposite()) {
			let t = r.length;
			if (i < t && e) {
				let a = Math.min(e, t - i);
				n && n.skip(r, i, i + a), e -= a, i += a;
			}
			if (i == t) a = !!r.breakAfter, {tile: r, index: i} = o.pop(), i++;
			else if (!e) break;
		} else if (a) {
			if (!e) break;
			n && n.break(), e--, a = !1;
		} else if (i == r.children.length) {
			if (!e && !o.length) break;
			n && n.leave(r), a = !!r.breakAfter, {tile: r, index: i} = o.pop(), i++;
		} else {
			let s = r.children[i], c = s.breakAfter;
			(t > 0 ? s.length <= e : s.length < e) && (!n || n.skip(s, 0, s.length) !== !1 || !s.isComposite) ? (a = !!c, i++, e -= s.length) : (o.push({
				tile: r,
				index: i
			}), r = s, i = 0, n && s.isComposite() && n.enter(s));
		}
		return this.tile = r, this.index = i, this.beforeBreak = a, this;
	}
	get root() {
		return this.parents.length ? this.parents[0].tile : this.tile;
	}
}, ki = class {
	constructor(e, t, n, r) {
		this.from = e, this.to = t, this.wrapper = n, this.rank = r;
	}
}, Ai = class {
	constructor(e, t, n) {
		this.cache = e, this.root = t, this.blockWrappers = n, this.curLine = null, this.lastBlock = null, this.afterWidget = null, this.pos = 0, this.wrappers = [], this.wrapperPos = 0;
	}
	addText(e, t, n, r) {
		var i;
		this.flushBuffer();
		let a = this.ensureMarks(t, n), o = a.lastChild;
		if (o && o.isText() && !(o.flags & 8) && o.length + e.length < 512) {
			this.cache.reused.set(o, 2);
			let t = a.children[a.children.length - 1] = new Ti(o.dom, o.text + e);
			t.parent = a;
		} else a.append(r || Ti.of(e, (i = this.cache.find(Ti)) == null ? void 0 : i.dom));
		this.pos += e.length, this.afterWidget = null;
	}
	addComposition(e, t) {
		let n = this.curLine;
		n.dom != t.line.dom && (n.setDOM(this.cache.reused.has(t.line) ? Bi(t.line.dom) : t.line.dom), this.cache.reused.set(t.line, 2));
		let r = n;
		for (let e = t.marks.length - 1; e >= 0; e--) {
			let n = t.marks[e], i = r.lastChild;
			if (i instanceof wi && i.mark.eq(n.mark)) i.dom != n.dom && i.setDOM(Bi(n.dom)), r = i;
			else {
				if (this.cache.reused.get(n)) {
					let e = G.get(n.dom);
					e && e.setDOM(Bi(n.dom));
				}
				let e = wi.of(n.mark, n.dom);
				r.append(e), r = e;
			}
			this.cache.reused.set(n, 2);
		}
		let i = G.get(e.text);
		i && this.cache.reused.set(i, 2);
		let a = new Ti(e.text, e.text.nodeValue);
		a.flags |= 8, this.pos = e.range.toB, r.append(a);
	}
	addInlineWidget(e, t, n) {
		let r = this.afterWidget && e.flags & 48 && (this.afterWidget.flags & 48) == (e.flags & 48);
		r || this.flushBuffer();
		let i = this.ensureMarks(t, n);
		!r && !(e.flags & 16) && i.append(this.getBuffer(1)), i.append(e), this.pos += e.length, this.afterWidget = e;
	}
	addMark(e, t, n) {
		this.flushBuffer(), this.ensureMarks(t, n).append(e), this.pos += e.length, this.afterWidget = null;
	}
	addBlockWidget(e) {
		this.getBlockPos().append(e), this.pos += e.length, this.lastBlock = e, this.endLine();
	}
	continueWidget(e) {
		let t = this.afterWidget || this.lastBlock;
		t.length += e, this.pos += e;
	}
	addLineStart(e, t) {
		var n;
		e || (e = Li);
		let r = xi.start(e, t || ((n = this.cache.find(xi)) == null ? void 0 : n.dom), !!t);
		this.getBlockPos().append(this.lastBlock = this.curLine = r);
	}
	addLine(e) {
		this.getBlockPos().append(e), this.pos += e.length, this.lastBlock = e, this.endLine();
	}
	addBreak() {
		this.lastBlock.flags |= 1, this.endLine(), this.pos++;
	}
	addLineStartIfNotCovered(e) {
		this.blockPosCovered() || this.addLineStart(e);
	}
	ensureLine(e) {
		this.curLine || this.addLineStart(e);
	}
	ensureMarks(e, t) {
		var n;
		let r = this.curLine;
		for (let i = e.length - 1; i >= 0; i--) {
			let a = e[i], o;
			if (t > 0 && (o = r.lastChild) && o instanceof wi && o.mark.eq(a)) r = o, t--;
			else {
				let e = wi.of(a, (n = this.cache.find(wi, (e) => e.mark.eq(a))) == null ? void 0 : n.dom);
				r.append(e), r = e, t = 0;
			}
		}
		return r;
	}
	endLine() {
		if (this.curLine) {
			this.flushBuffer();
			let e = this.curLine.lastChild;
			(!e || !Fi(this.curLine, !1) || e.dom.nodeName != "BR" && e.isWidget() && !(R.ios && Fi(this.curLine, !0))) && this.curLine.append(this.cache.findWidget(Hi, 0, 32) || new Ei(Hi.toDOM(), 0, Hi, 32)), this.curLine = this.afterWidget = null;
		}
	}
	updateBlockWrappers() {
		this.wrapperPos > this.pos + 1e4 && (this.blockWrappers.goto(this.pos), this.wrappers.length = 0);
		for (let e = this.wrappers.length - 1; e >= 0; e--) this.wrappers[e].to < this.pos && this.wrappers.splice(e, 1);
		for (let e = this.blockWrappers; e.value && e.from <= this.pos; e.next()) if (e.to >= this.pos) {
			let t = e.rank * 102 + e.value.rank, n = new ki(e.from, e.to, e.value, t), r = this.wrappers.length;
			for (; r > 0 && (this.wrappers[r - 1].rank - n.rank || this.wrappers[r - 1].to - n.to) < 0;) r--;
			this.wrappers.splice(r, 0, n);
		}
		this.wrapperPos = this.pos;
	}
	getBlockPos() {
		var e;
		this.updateBlockWrappers();
		let t = this.root;
		for (let n of this.wrappers) {
			let r = t.lastChild;
			if (n.from < this.pos && r instanceof bi && r.wrapper.eq(n.wrapper)) t = r;
			else {
				let r = bi.of(n.wrapper, (e = this.cache.find(bi, (e) => e.wrapper.eq(n.wrapper))) == null ? void 0 : e.dom);
				t.append(r), t = r;
			}
		}
		return t;
	}
	blockPosCovered() {
		let e = this.lastBlock;
		return e != null && !e.breakAfter && (!e.isWidget() || (e.flags & 160) > 0);
	}
	getBuffer(e) {
		let t = 2 | (e < 0 ? 16 : 32), n = this.cache.find(Di, void 0, 1);
		return n && (n.flags = t), n || new Di(t);
	}
	flushBuffer() {
		this.afterWidget && !(this.afterWidget.flags & 32) && (this.afterWidget.parent.append(this.getBuffer(-1)), this.afterWidget = null);
	}
}, ji = class {
	constructor(e) {
		this.skipCount = 0, this.text = "", this.textOff = 0, this.cursor = e.iter();
	}
	skip(e) {
		this.textOff + e <= this.text.length ? this.textOff += e : (this.skipCount += e - (this.text.length - this.textOff), this.text = "", this.textOff = 0);
	}
	next(e) {
		if (this.textOff == this.text.length) {
			let { value: t, lineBreak: n, done: r } = this.cursor.next(this.skipCount);
			if (this.skipCount = 0, r) throw Error("Ran out of text content when drawing inline views");
			this.text = t;
			let i = this.textOff = Math.min(e, t.length);
			return n ? null : t.slice(0, i);
		}
		let t = Math.min(this.text.length, this.textOff + e), n = this.text.slice(this.textOff, t);
		return this.textOff = t, n;
	}
}, Mi = [
	Ei,
	xi,
	Ti,
	wi,
	Di,
	bi,
	yi
];
for (let e = 0; e < Mi.length; e++) Mi[e].bucket = e;
var Ni = class {
	constructor(e) {
		this.view = e, this.buckets = Mi.map(() => []), this.index = Mi.map(() => 0), this.reused = /* @__PURE__ */ new Map();
	}
	add(e) {
		let t = e.constructor.bucket, n = this.buckets[t];
		n.length < 6 ? n.push(e) : n[this.index[t] = (this.index[t] + 1) % 6] = e;
	}
	find(e, t, n = 2) {
		let r = e.bucket, i = this.buckets[r], a = this.index[r];
		for (let e = 0; e < i.length; e++) {
			let o = (e + a) % i.length, s = i[o];
			if ((!t || t(s)) && !this.reused.has(s)) return i.splice(o, 1), o < a && this.index[r]--, this.reused.set(s, n), s;
		}
		return null;
	}
	findWidget(e, t, n) {
		let r = this.buckets[0];
		if (r.length) for (let i = 0, a = 0;; i++) {
			if (i == r.length) {
				if (a) return null;
				a = 1, i = 0;
			}
			let o = r[i];
			if (!this.reused.has(o) && (a == 0 ? o.widget.compare(e) : o.widget.constructor == e.constructor && e.updateDOM(o.dom, this.view, o.widget))) return r.splice(i, 1), i < this.index[0] && this.index[0]--, o.widget == e && o.length == t && (o.flags & 497) == n ? (this.reused.set(o, 1), o) : (this.reused.set(o, 2), new Ei(o.dom, t, e, o.flags & -498 | n));
		}
	}
	reuse(e) {
		return this.reused.set(e, 1), e;
	}
	maybeReuse(e, t = 2) {
		if (!this.reused.has(e)) return this.reused.set(e, t), e.dom;
	}
	clear() {
		for (let e = 0; e < this.buckets.length; e++) this.buckets[e].length = this.index[e] = 0;
	}
}, Pi = class {
	constructor(e, t, n, r, i) {
		this.view = e, this.decorations = r, this.disallowBlockEffectsFor = i, this.openWidget = !1, this.openMarks = 0, this.cache = new Ni(e), this.text = new ji(e.state.doc), this.builder = new Ai(this.cache, new yi(e, e.contentDOM), P.iter(n)), this.cache.reused.set(t, 2), this.old = new Oi(t), this.reuseWalker = {
			skip: (e, t, n) => {
				if (this.cache.add(e), e.isComposite()) return !1;
			},
			enter: (e) => this.cache.add(e),
			leave: () => {},
			break: () => {}
		};
	}
	run(e, t) {
		let n = t && this.getCompositionContext(t.text);
		for (let r = 0, i = 0, a = 0;;) {
			let o = a < e.length ? e[a++] : null, s = o ? o.fromA : this.old.root.length;
			if (s > r) {
				let e = s - r;
				this.preserve(e, !a, !o), r = s, i += e;
			}
			if (!o) break;
			t && o.fromA <= t.range.fromA && o.toA >= t.range.toA ? (this.forward(o.fromA, t.range.fromA, t.range.fromA < t.range.toA ? 1 : -1), this.emit(i, t.range.fromB), this.builder.flushBuffer(), this.cache.clear(), this.builder.addComposition(t, n), this.text.skip(t.range.toB - t.range.fromB), this.forward(t.range.fromA, o.toA), this.emit(t.range.toB, o.toB)) : (this.forward(o.fromA, o.toA), this.emit(i, o.toB)), i = o.toB, r = o.toA;
		}
		return this.builder.curLine && this.builder.endLine(), this.builder.root;
	}
	preserve(e, t, n) {
		let r = zi(this.old), i = this.openMarks;
		this.old.advance(e, n ? 1 : -1, {
			skip: (e, t, n) => {
				if (e.isWidget()) {
					if (this.openWidget) this.builder.continueWidget(n - t);
					else {
						let a = n > 0 || t < e.length ? Ei.of(e.widget, this.view, n - t, e.flags & 496, this.cache.maybeReuse(e)) : this.cache.reuse(e);
						a.flags & 256 ? (a.flags &= -2, this.builder.addBlockWidget(a)) : (this.builder.ensureLine(null), this.builder.addInlineWidget(a, r, i), i = r.length);
					}
				} else if (e.isText()) this.builder.ensureLine(null), !t && n == e.length && !this.cache.reused.has(e) ? this.builder.addText(e.text, r, i, this.cache.reuse(e)) : (this.cache.add(e), this.builder.addText(e.text.slice(t, n), r, i)), i = r.length;
				else if (e.isLine()) e.flags &= -2, this.cache.reused.set(e, 1), this.builder.addLine(e);
				else if (e instanceof Di) this.cache.add(e);
				else if (e instanceof wi) this.builder.ensureLine(null), this.builder.addMark(e, r, i), this.cache.reused.set(e, 1), i = r.length;
				else return !1;
				this.openWidget = !1;
			},
			enter: (e) => {
				e.isLine() ? this.builder.addLineStart(e.attrs, this.cache.maybeReuse(e)) : (this.cache.add(e), e instanceof wi && r.unshift(e.mark)), this.openWidget = !1;
			},
			leave: (e) => {
				e.isLine() ? r.length && (r.length = i = 0) : e instanceof wi && (r.shift(), i = Math.min(i, r.length));
			},
			break: () => {
				this.builder.addBreak(), this.openWidget = !1;
			}
		}), this.text.skip(e);
	}
	emit(e, t) {
		let n = null, r = this.builder, i = -1, a = P.spans(this.decorations, e, t, {
			point: (e, t, a, o, s, c) => {
				if (a instanceof Rn) {
					if (this.disallowBlockEffectsFor[c]) {
						if (a.block) throw RangeError("Block decorations may not be specified via plugins");
						if (t > this.view.state.doc.lineAt(e).to) throw RangeError("Decorations that replace line breaks may not be specified via plugins");
					}
					if (i = o.length, s > o.length) r.continueWidget(t - e);
					else {
						let i = a.widget || (a.block ? Vi.block : Vi.inline), c = Ii(a), l = this.cache.findWidget(i, t - e, c) || Ei.of(i, this.view, t - e, c);
						a.block ? (a.startSide > 0 && r.addLineStartIfNotCovered(n), r.addBlockWidget(l)) : (r.ensureLine(n), r.addInlineWidget(l, o, s));
					}
					n = null;
				} else n = Ri(n, a);
				t > e && this.text.skip(t - e);
			},
			span: (e, t, a, o) => {
				for (let i = e; i < t;) {
					let s = this.text.next(Math.min(512, t - i));
					s == null ? (r.addLineStartIfNotCovered(n), r.addBreak(), i++) : (r.ensureLine(n), r.addText(s, a, i == e ? o : a.length), i += s.length), n = null;
				}
				i = a.length;
			}
		});
		i > -1 && (this.openWidget = a > i), this.openWidget || r.addLineStartIfNotCovered(n), this.openMarks = a;
	}
	forward(e, t, n = 1) {
		t - e <= 10 ? this.old.advance(t - e, n, this.reuseWalker) : (this.old.advance(5, -1, this.reuseWalker), this.old.advance(t - e - 10, -1), this.old.advance(5, n, this.reuseWalker));
	}
	getCompositionContext(e) {
		let t = [], n = null;
		for (let r = e.parentNode;; r = r.parentNode) {
			let e = G.get(r);
			if (r == this.view.contentDOM) break;
			e instanceof wi ? t.push(e) : e != null && e.isLine() ? n = e : e instanceof bi || (r.nodeName == "DIV" && !n && r != this.view.contentDOM ? n = new xi(r, Li) : n || t.push(wi.of(new In({
				tagName: r.nodeName.toLowerCase(),
				attributes: Pn(r)
			}), r)));
		}
		return {
			line: n,
			marks: t
		};
	}
};
function Fi(e, t) {
	let n = (e) => {
		for (let r of e.children) if ((t ? r.isText() : r.length) || n(r)) return !0;
		return !1;
	};
	return n(e);
}
function Ii(e) {
	let t = e.isReplace ? (e.startSide < 0 ? 64 : 0) | (e.endSide > 0 ? 128 : 0) : e.startSide > 0 ? 32 : 16;
	return e.block && (t |= 256), t;
}
var Li = { class: "cm-line" };
function Ri(e, t) {
	let n = t.spec.attributes, r = t.spec.class;
	return !n && !r ? e : (e || (e = { class: "cm-line" }), n && kn(n, e), r && (e.class += " " + r), e);
}
function zi(e) {
	let t = [];
	for (let n = e.parents.length; n > 1; n--) {
		let r = n == e.parents.length ? e.tile : e.parents[n].tile;
		r instanceof wi && t.push(r.mark);
	}
	return t;
}
function Bi(e) {
	let t = G.get(e);
	return t && t.setDOM(e.cloneNode()), e;
}
var Vi = class extends Fn {
	constructor(e) {
		super(), this.tag = e;
	}
	eq(e) {
		return e.tag == this.tag;
	}
	toDOM() {
		return document.createElement(this.tag);
	}
	updateDOM(e) {
		return e.nodeName.toLowerCase() == this.tag;
	}
	get isHidden() {
		return !0;
	}
};
Vi.inline = /*@__PURE__*/ new Vi("span"), Vi.block = /*@__PURE__*/ new Vi("div");
var Hi = /*@__PURE__*/ new class extends Fn {
	toDOM() {
		return document.createElement("br");
	}
	get isHidden() {
		return !0;
	}
	get editable() {
		return !0;
	}
}(), Ui = class {
	constructor(e) {
		this.view = e, this.decorations = [], this.blockWrappers = [], this.dynamicDecorationMap = [!1], this.domChanged = null, this.hasComposition = null, this.editContextFormatting = B.none, this.lastCompositionAfterCursor = !1, this.minWidth = 0, this.minWidthFrom = 0, this.minWidthTo = 0, this.impreciseAnchor = null, this.impreciseHead = null, this.forceSelection = !1, this.lastUpdate = Date.now(), this.updateDeco(), this.tile = new yi(e, e.contentDOM), this.updateInner([new mi(0, 0, 0, e.state.doc.length)], null);
	}
	update(e) {
		var t;
		let n = e.changedRanges;
		this.minWidth > 0 && n.length && (n.every(({ fromA: e, toA: t }) => t < this.minWidthFrom || e > this.minWidthTo) ? (this.minWidthFrom = e.changes.mapPos(this.minWidthFrom, 1), this.minWidthTo = e.changes.mapPos(this.minWidthTo, 1)) : this.minWidth = this.minWidthFrom = this.minWidthTo = 0), this.updateEditContextFormatting(e);
		let r = -1;
		this.view.inputState.composing >= 0 && !this.view.observer.editContext && ((t = this.domChanged) != null && t.newSel ? r = this.domChanged.newSel.head : !ea(e.changes, this.hasComposition) && !e.selectionSet && (r = e.state.selection.main.head));
		let i = r > -1 ? qi(this.view, e.changes, r) : null;
		if (this.domChanged = null, this.hasComposition) {
			let { from: t, to: r } = this.hasComposition;
			n = new mi(t, r, e.changes.mapPos(t, -1), e.changes.mapPos(r, 1)).addToSet(n.slice());
		}
		this.hasComposition = i ? {
			from: i.range.fromB,
			to: i.range.toB
		} : null, (R.ie || R.chrome) && !i && e && e.state.doc.lines != e.startState.doc.lines && (this.forceSelection = !0);
		let a = this.decorations, o = this.blockWrappers;
		this.updateDeco();
		let s = Xi(a, this.decorations, e.changes);
		s.length && (n = mi.extendWithRanges(n, s));
		let c = Qi(o, this.blockWrappers, e.changes);
		return c.length && (n = mi.extendWithRanges(n, c)), i && !n.some((e) => e.fromA <= i.range.fromA && e.toA >= i.range.toA) && (n = i.range.addToSet(n.slice())), this.tile.flags & 2 && n.length == 0 ? !1 : (this.updateInner(n, i), e.transactions.length && (this.lastUpdate = Date.now()), !0);
	}
	updateInner(e, t) {
		this.view.viewState.mustMeasureContent = !0;
		let { observer: n } = this.view;
		n.ignore(() => {
			if (t || e.length) {
				let n = this.tile, r = new Pi(this.view, n, this.blockWrappers, this.decorations, this.dynamicDecorationMap);
				t && G.get(t.text) && r.cache.reused.set(G.get(t.text), 2), this.tile = r.run(e, t), Wi(n, r.cache.reused);
			}
			this.tile.dom.style.height = this.view.viewState.contentHeight / this.view.scaleY + "px", this.tile.dom.style.flexBasis = this.minWidth ? this.minWidth + "px" : "";
			let r = R.chrome || R.ios ? {
				node: n.selectionRange.focusNode,
				written: !1
			} : void 0;
			this.tile.sync(r), r && (r.written || n.selectionRange.focusNode != r.node || !this.tile.dom.contains(r.node)) && (this.forceSelection = !0), this.tile.dom.style.height = "";
		});
		let r = [];
		if (this.view.viewport.from || this.view.viewport.to < this.view.state.doc.length) for (let e of this.tile.children) e.isWidget() && e.widget instanceof ta && r.push(e.dom);
		n.updateGaps(r);
	}
	updateEditContextFormatting(e) {
		this.editContextFormatting = this.editContextFormatting.map(e.changes);
		for (let t of e.transactions) for (let e of t.effects) e.is(Qr) && (this.editContextFormatting = e.value);
	}
	updateSelection(e = !1, t = !1) {
		(e || !this.view.observer.selectionRange.focusNode) && this.view.observer.readSelectionRange();
		let { dom: n } = this.tile, r = this.view.root.activeElement, i = r == n, a = !i && !(this.view.state.facet($r) || n.tabIndex > -1) && Gn(n, this.view.observer.selectionRange) && !(r && n.contains(r));
		if (!(i || t || a)) return;
		let o = this.forceSelection;
		this.forceSelection = !1;
		let s = this.view.state.selection.main, c, l;
		if (s.empty ? l = c = this.inlineDOMNearPos(s.anchor, s.assoc || 1) : (l = this.inlineDOMNearPos(s.head, s.head == s.from ? 1 : -1), c = this.inlineDOMNearPos(s.anchor, s.anchor == s.from ? 1 : -1)), R.gecko && s.empty && !this.hasComposition && Gi(c)) {
			let e = document.createTextNode("");
			this.view.observer.ignore(() => c.node.insertBefore(e, c.node.childNodes[c.offset] || null)), c = l = new gr(e, 0), o = !0;
		}
		let u = this.view.observer.selectionRange;
		(o || !u.focusNode || (!qn(c.node, c.offset, u.anchorNode, u.anchorOffset) || !qn(l.node, l.offset, u.focusNode, u.focusOffset)) && !this.suppressWidgetCursorChange(u, s)) && (this.view.observer.ignore(() => {
			R.android && R.chrome && n.contains(u.focusNode) && $i(u.focusNode, n) && (n.blur(), n.focus({ preventScroll: !0 }));
			let e = Un(this.view.root);
			if (e) {
				if (s.empty) {
					if (R.gecko) {
						let e = Ji(c.node, c.offset);
						if (e && e != 3) {
							let t = (e == 1 ? mr : hr)(c.node, c.offset);
							t && (c = new gr(t.node, t.offset));
						}
					}
					e.collapse(c.node, c.offset), s.bidiLevel != null && e.caretBidiLevel !== void 0 && (e.caretBidiLevel = s.bidiLevel);
				} else if (e.extend) {
					e.collapse(c.node, c.offset);
					try {
						e.extend(l.node, l.offset);
					} catch (e) {}
				} else {
					let t = document.createRange();
					s.anchor > s.head && ([c, l] = [l, c]), t.setEnd(l.node, l.offset), t.setStart(c.node, c.offset), e.removeAllRanges(), e.addRange(t);
				}
			}
			a && this.view.root.activeElement == n && (n.blur(), r && r.focus());
		}), this.view.observer.setSelectionRange(c, l)), this.impreciseAnchor = c.precise ? null : new gr(u.anchorNode, u.anchorOffset), this.impreciseHead = l.precise ? null : new gr(u.focusNode, u.focusOffset);
	}
	suppressWidgetCursorChange(e, t) {
		return this.hasComposition && t.empty && qn(e.focusNode, e.focusOffset, e.anchorNode, e.anchorOffset) && this.posFromDOM(e.focusNode, e.focusOffset) == t.head;
	}
	enforceCursorAssoc() {
		if (this.hasComposition) return;
		let { view: e } = this, t = e.state.selection.main, n = Un(e.root), { anchorNode: r, anchorOffset: i } = e.observer.selectionRange;
		if (!n || !t.empty || !t.assoc || !n.modify) return;
		let a = this.lineAt(t.head, t.assoc);
		if (!a) return;
		let o = a.posAtStart;
		if (t.head == o || t.head == o + a.length) return;
		let s = this.coordsAt(t.head, -1), c = this.coordsAt(t.head, 1);
		if (!s || !c || s.bottom > c.top) return;
		let l = this.domAtPos(t.head + t.assoc, t.assoc);
		n.collapse(l.node, l.offset), n.modify("move", t.assoc < 0 ? "forward" : "backward", "lineboundary"), e.observer.readSelectionRange();
		let u = e.observer.selectionRange;
		e.docView.posFromDOM(u.anchorNode, u.anchorOffset) != t.from && n.collapse(r, i);
	}
	posFromDOM(e, t) {
		let n = this.tile.nearest(e);
		if (!n) return this.tile.dom.compareDocumentPosition(e) & 2 ? 0 : this.view.state.doc.length;
		let r = n.posAtStart;
		if (n.isComposite()) {
			let i;
			if (e == n.dom) i = n.dom.childNodes[t];
			else {
				let r = Zn(e) == 0 ? 0 : t == 0 ? -1 : 1;
				for (;;) {
					let t = e.parentNode;
					if (t == n.dom) break;
					r == 0 && t.firstChild != t.lastChild && (r = e == t.firstChild ? -1 : 1), e = t;
				}
				i = r < 0 ? e : e.nextSibling;
			}
			if (i == n.dom.firstChild) return r;
			for (; i && !G.get(i);) i = i.nextSibling;
			if (!i) return r + n.length;
			for (let e = 0, t = r;; e++) {
				let r = n.children[e];
				if (r.dom == i) return t;
				t += r.length + r.breakAfter;
			}
		} else if (n.isText()) return e == n.dom ? r + t : r + (t ? n.length : 0);
		else return r;
	}
	domAtPos(e, t) {
		let { tile: n, offset: r } = this.tile.resolveBlock(e, t);
		return n.isWidget() ? n.domPosFor(r, t) : n.domIn(r, t);
	}
	inlineDOMNearPos(e, t) {
		let n, r = -1, i = !1, a, o = -1, s = !1;
		return this.tile.blockTiles((t, c) => {
			if (t.isWidget()) {
				if (t.flags & 32 && c >= e) return !0;
				t.flags & 16 && (i = !0);
			} else {
				let l = c + t.length;
				if (c <= e && (n = t, r = e - c, i = l < e), l >= e && !a && (a = t, o = e - c, s = c > e), c > e && a) return !0;
			}
		}), !n && !a ? this.domAtPos(e, t) : (i && a ? n = null : s && n && (a = null), n && t < 0 || !a ? n.domIn(r, t) : a.domIn(o, t));
	}
	coordsAt(e, t, n) {
		let { tile: r, offset: i } = this.tile.resolveBlock(e, t);
		return r.isWidget() ? r.widget instanceof ta ? null : r.coordsInWidget(i, t, !0) : r.coordsIn(i, t, n);
	}
	lineAt(e, t) {
		let { tile: n } = this.tile.resolveBlock(e, t);
		return n.isLine() ? n : null;
	}
	coordsForChar(e) {
		let { tile: t, offset: n } = this.tile.resolveBlock(e, 1);
		if (!t.isLine()) return null;
		function r(e, t) {
			if (e.isComposite()) for (let n of e.children) {
				if (n.length >= t) {
					let e = r(n, t);
					if (e) return e;
				}
				if (t -= n.length, t < 0) break;
			}
			else if (e.isText() && t < e.length) {
				let n = w(e.text, t);
				if (n == t) return null;
				let r = lr(e.dom, t, n).getClientRects();
				for (let e = 0; e < r.length; e++) {
					let t = r[e];
					if (e == r.length - 1 || t.top < t.bottom && t.left < t.right) return t;
				}
			}
			return null;
		}
		return r(t, n);
	}
	measureVisibleLineHeights(e) {
		let t = [], { from: n, to: r } = e, i = this.view.contentDOM.clientWidth, a = i > Math.max(this.view.scrollDOM.clientWidth, this.minWidth) + 1, o = -1, s = this.view.textDirection == V.LTR, c = 0, l = (e, u, d) => {
			for (let f = 0; f < e.children.length && !(u > r); f++) {
				let r = e.children[f], p = u + r.length, m = r.dom.getBoundingClientRect(), { height: h } = m;
				if (d && !f && (c += m.top - d.top), r instanceof bi) p > n && l(r, u, m);
				else if (u >= n && (c > 0 && t.push(-c), t.push(h + c), c = 0, a)) {
					let e = r.dom.lastChild, t = e ? Kn(e) : [];
					if (t.length) {
						let e = t[t.length - 1], n = s ? e.right - m.left : m.right - e.left;
						n > o && (o = n, this.minWidth = i, this.minWidthFrom = u, this.minWidthTo = p);
					}
				}
				d && f == e.children.length - 1 && (c += d.bottom - m.bottom), u = p + r.breakAfter;
			}
		};
		return l(this.tile, 0, null), t;
	}
	textDirectionAt(e) {
		let { tile: t } = this.tile.resolveBlock(e, 1);
		return getComputedStyle(t.dom).direction == "rtl" ? V.RTL : V.LTR;
	}
	measureTextSize() {
		let e = this.tile.blockTiles((e) => {
			if (e.isLine() && e.children.length && e.length <= 20) {
				let t = 0, n;
				for (let r of e.children) {
					if (!r.isText() || /[^ -~]/.test(r.text)) return;
					let e = Kn(r.dom);
					if (e.length != 1) return;
					t += e[0].width, n = e[0].height;
				}
				if (t) return {
					lineHeight: e.dom.getBoundingClientRect().height,
					charWidth: t / e.length,
					textHeight: n
				};
			}
		});
		if (e) return e;
		let t = document.createElement("div"), n, r, i;
		return t.className = "cm-line", t.style.width = "99999px", t.style.position = "absolute", t.textContent = "abc def ghi jkl mno pqr stu", this.view.observer.ignore(() => {
			this.tile.dom.appendChild(t);
			let e = Kn(t.firstChild)[0];
			n = t.getBoundingClientRect().height, r = e && e.width ? e.width / 27 : 7, i = e && e.height ? e.height : n, t.remove();
		}), {
			lineHeight: n,
			charWidth: r,
			textHeight: i
		};
	}
	computeBlockGapDeco() {
		let e = [], t = this.view.viewState;
		for (let n = 0, r = 0;; r++) {
			let i = r == t.viewports.length ? null : t.viewports[r], a = i ? i.from - 1 : this.view.state.doc.length;
			if (a > n) {
				let r = (t.lineBlockAt(a).bottom - t.lineBlockAt(n).top) / this.view.scaleY;
				e.push(B.replace({
					widget: new ta(r),
					block: !0,
					inclusive: !0,
					isBlockGap: !0
				}).range(n, a));
			}
			if (!i) break;
			n = i.to + 1;
		}
		return B.set(e);
	}
	updateDeco() {
		let e = 1, t = this.view.state.facet(ai).map((t) => (this.dynamicDecorationMap[e++] = typeof t == "function") ? t(this.view) : t), n = !1, r = this.view.state.facet(si).map((e, t) => {
			let r = typeof e == "function";
			return r && (n = !0), r ? e(this.view) : e;
		});
		for (r.length && (this.dynamicDecorationMap[e++] = n, t.push(P.join(r))), this.decorations = [
			this.editContextFormatting,
			...t,
			this.computeBlockGapDeco(),
			this.view.viewState.lineGapDeco
		]; e < this.decorations.length;) this.dynamicDecorationMap[e++] = !1;
		this.blockWrappers = this.view.state.facet(oi).map((e) => typeof e == "function" ? e(this.view) : e);
	}
	scrollIntoView(e) {
		if (e.isSnapshot) {
			let t = this.view.viewState.lineBlockAt(e.range.head);
			this.view.scrollDOM.scrollTop = t.top - e.yMargin, this.view.scrollDOM.scrollLeft = e.xMargin;
			return;
		}
		for (let t of this.view.state.facet(Yr)) try {
			if (t(this.view, e.range, e)) return !0;
		} catch (e) {
			U(this.view.state, e, "scroll handler");
		}
		let { range: t } = e, n = this.coordsAt(t.head, t.assoc || (t.head > t.anchor ? -1 : 1)), r;
		if (!n) return;
		!t.empty && (r = this.coordsAt(t.anchor, t.anchor > t.head ? -1 : 1)) && (n = {
			left: Math.min(n.left, r.left),
			top: Math.min(n.top, r.top),
			right: Math.max(n.right, r.right),
			bottom: Math.max(n.bottom, r.bottom)
		});
		let i = fi(this.view), a = {
			left: n.left - i.left,
			top: n.top - i.top,
			right: n.right + i.right,
			bottom: n.bottom + i.bottom
		}, { offsetWidth: o, offsetHeight: s } = this.view.scrollDOM;
		if (tr(this.view.scrollDOM, a, t.head < t.anchor ? -1 : 1, e.x, e.y, Math.max(Math.min(e.xMargin, o), -o), Math.max(Math.min(e.yMargin, s), -s), this.view.textDirection == V.LTR), window.visualViewport && window.innerHeight - window.visualViewport.height > 1 && (n.top > window.visualViewport.offsetTop + window.visualViewport.height || n.bottom < window.visualViewport.offsetTop)) {
			let e = this.view.docView.lineAt(t.head, 1);
			if (e) {
				let t = ir(e.dom);
				e.dom.scrollIntoView({ block: "nearest" }), ar(t, !1);
			}
		}
	}
	lineHasWidget(e) {
		let t = (e) => e.isWidget() || e.children.some(t);
		return t(this.tile.resolveBlock(e, 1).tile);
	}
	destroy() {
		Wi(this.tile);
	}
};
function Wi(e, t) {
	let n = t == null ? void 0 : t.get(e);
	if (n != 1) {
		n == null && e.destroy();
		for (let n of e.children) Wi(n, t);
	}
}
function Gi(e) {
	return e.node.nodeType == 1 && e.node.firstChild && (e.offset == 0 || e.node.childNodes[e.offset - 1].contentEditable == "false") && (e.offset == e.node.childNodes.length || e.node.childNodes[e.offset].contentEditable == "false");
}
function Ki(e, t) {
	let n = e.observer.selectionRange;
	if (!n.focusNode) return null;
	let r = mr(n.focusNode, n.focusOffset), i = hr(n.focusNode, n.focusOffset), a = r || i;
	if (i && r && i.node != r.node) {
		let t = G.get(i.node);
		if (!t || t.isText() && t.text != i.node.nodeValue) a = i;
		else if (e.docView.lastCompositionAfterCursor) {
			let e = G.get(r.node);
			!e || e.isText() && e.text != r.node.nodeValue || (a = i);
		}
	}
	if (e.docView.lastCompositionAfterCursor = a != r, !a) return null;
	let o = t - a.offset;
	return {
		from: o,
		to: o + a.node.nodeValue.length,
		node: a.node
	};
}
function qi(e, t, n) {
	let r = Ki(e, n);
	if (!r) return null;
	let { node: i, from: a, to: o } = r, s = i.nodeValue;
	if (/[\n\r]/.test(s) || e.state.doc.sliceString(r.from, r.to) != s) return null;
	let c = t.invertedDesc;
	return {
		range: new mi(c.mapPos(a), c.mapPos(o), a, o),
		text: i
	};
}
function Ji(e, t) {
	return e.nodeType == 1 ? (t && e.childNodes[t - 1].contentEditable == "false" ? 1 : 0) | (t < e.childNodes.length && e.childNodes[t].contentEditable == "false" ? 2 : 0) : 0;
}
var Yi = class {
	constructor() {
		this.changes = [];
	}
	compareRange(e, t) {
		Vn(e, t, this.changes);
	}
	comparePoint(e, t) {
		Vn(e, t, this.changes);
	}
	boundChange(e) {
		Vn(e, e, this.changes);
	}
};
function Xi(e, t, n) {
	let r = new Yi();
	return P.compare(e, t, n, r), r.changes;
}
var Zi = class {
	constructor() {
		this.changes = [];
	}
	compareRange(e, t) {
		Vn(e, t, this.changes);
	}
	comparePoint() {}
	boundChange(e) {
		Vn(e, e, this.changes);
	}
};
function Qi(e, t, n) {
	let r = new Zi();
	return P.compare(e, t, n, r), r.changes;
}
function $i(e, t) {
	for (let n = e; n && n != t; n = n.assignedSlot || n.parentNode) if (n.nodeType == 1 && n.contentEditable == "false") return !0;
	return !1;
}
function ea(e, t) {
	let n = !1;
	return t && e.iterChangedRanges((e, r) => {
		e < t.to && r > t.from && (n = !0);
	}), n;
}
var ta = class extends Fn {
	constructor(e) {
		super(), this.height = e;
	}
	toDOM() {
		let e = document.createElement("div");
		return e.className = "cm-gap", this.updateDOM(e), e;
	}
	eq(e) {
		return e.height == this.height;
	}
	updateDOM(e) {
		return e.style.height = this.height + "px", !0;
	}
	get editable() {
		return !0;
	}
	get estimatedHeight() {
		return this.height;
	}
	ignoreEvent() {
		return !1;
	}
};
function na(e, t, n = 1) {
	let r = e.charCategorizer(t), i = e.doc.lineAt(t), a = t - i.from;
	if (i.length == 0) return D.cursor(t);
	a == 0 ? n = 1 : a == i.length && (n = -1);
	let o = a, s = a;
	n < 0 ? o = w(i.text, a, !1) : s = w(i.text, a);
	let c = r(i.text.slice(o, s));
	for (; o > 0;) {
		let e = w(i.text, o, !1);
		if (r(i.text.slice(e, o)) != c) break;
		o = e;
	}
	for (; s < i.length;) {
		let e = w(i.text, s);
		if (r(i.text.slice(s, e)) != c) break;
		s = e;
	}
	return D.undirectionalRange(o + i.from, s + i.from);
}
function ra(e, t, n, r, i) {
	let a = Math.round((r - t.left) * e.defaultCharacterWidth);
	if (e.lineWrapping && n.height > e.defaultLineHeight * 1.5) {
		let t = e.viewState.heightOracle.textHeight, r = Math.floor((i - n.top - (e.defaultLineHeight - t) * .5) / t);
		a += r * e.viewState.heightOracle.lineLength;
	}
	let o = e.state.sliceDoc(n.from, n.to);
	return n.from + Zt(o, a, e.state.tabSize);
}
function ia(e, t, n) {
	let r = e.lineBlockAt(t);
	if (Array.isArray(r.type)) {
		let e;
		for (let i of r.type) {
			if (i.from > t) break;
			if (!(i.to < t)) {
				if (i.from < t && i.to > t) return i;
				(!e || i.type == z.Text && (e.type != i.type || (n < 0 ? i.from < t : i.to > t))) && (e = i);
			}
		}
		return e || r;
	}
	return r;
}
function aa(e, t, n, r) {
	let i = ia(e, t.head, t.assoc || -1), a = !r || i.type != z.Text || !(e.lineWrapping || i.widgetLineBreaks) ? null : e.coordsAtPos(t.assoc < 0 && t.head > i.from ? t.head - 1 : t.head);
	if (a) {
		let t = e.dom.getBoundingClientRect(), r = e.textDirectionAt(i.from), o = e.posAtCoords({
			x: n == (r == V.LTR) ? t.right - 1 : t.left + 1,
			y: (a.top + a.bottom) / 2
		});
		if (o != null) return D.cursor(o, n ? -1 : 1);
	}
	return D.cursor(n ? i.to : i.from, n ? -1 : 1);
}
function oa(e, t, n, r) {
	let i = e.state.doc.lineAt(t.head), a = e.bidiSpans(i), o = e.textDirectionAt(i.from);
	for (let s = t, c = null;;) {
		let t = Ir(i, a, o, s, n), l = Fr;
		if (!t) {
			if (i.number == (n ? e.state.doc.lines : 1)) return s;
			l = "\n", i = e.state.doc.line(i.number + (n ? 1 : -1)), a = e.bidiSpans(i), t = e.visualLineSide(i, !n);
		}
		if (!c) {
			if (!r) return t;
			c = r(l);
		} else if (!c(l)) return s;
		s = t;
	}
}
function sa(e, t, n) {
	let r = e.state.charCategorizer(t), i = r(n);
	return (e) => {
		let t = r(e);
		return i == M.Space && (i = t), i == t;
	};
}
function ca(e, t, n, r) {
	let i = t.head, a = n ? 1 : -1;
	if (i == (n ? e.state.doc.length : 0)) return D.cursor(i, t.assoc);
	let o = t.goalColumn, s, c = e.contentDOM.getBoundingClientRect(), l = e.coordsAtPos(i, t.assoc || ((t.empty ? n : t.head == t.from) ? 1 : -1)), u = e.documentTop;
	if (l) o == null && (o = l.left - c.left), s = a < 0 ? l.top : l.bottom;
	else {
		let t = e.viewState.lineBlockAt(i);
		o == null && (o = Math.min(c.right - c.left, e.defaultCharacterWidth * (i - t.from))), s = (a < 0 ? t.top : t.bottom) + u;
	}
	let d = c.left + o, f = e.viewState.heightOracle.textHeight >> 1, p = r == null ? f : r;
	for (let t = 0;; t += f) {
		let r = s + (p + t) * a, i = pa(e, {
			x: d,
			y: r
		}, !1, a);
		if (n ? r > c.bottom : r < c.top) return D.cursor(i.pos, i.assoc);
		let l = e.coordsAtPos(i.pos, i.assoc), u = l ? (l.top + l.bottom) / 2 : 0;
		if (!l || (n ? u > s : u < s)) return D.cursor(i.pos, i.assoc, void 0, o);
	}
}
function la(e, t, n) {
	for (;;) {
		let r = 0;
		for (let i of e) i.between(t - 1, t + 1, (e, i, a) => {
			if (t > e && t < i) {
				let a = r || n || (t - e < i - t ? -1 : 1);
				t = a < 0 ? e : i, r = a;
			}
		});
		if (!r) return t;
	}
}
function ua(e, t) {
	let n = null;
	for (let r = 0; r < t.ranges.length; r++) {
		let i = t.ranges[r], a = null;
		if (i.empty) {
			let t = la(e, i.from, 0);
			t != i.from && (a = D.cursor(t, -1));
		} else {
			let t = la(e, i.from, -1), n = la(e, i.to, 1);
			(t != i.from || n != i.to) && (a = i.undirectional ? D.undirectionalRange(i.from, i.to) : D.range(i.from == i.anchor ? t : n, i.from == i.head ? t : n));
		}
		a && (n || (n = t.ranges.slice()), n[r] = a);
	}
	return n ? D.create(n, t.mainIndex) : t;
}
function da(e, t, n) {
	let r = la(e.state.facet(ci).map((t) => t(e)), n.from, t.head > n.from ? -1 : 1);
	return r == n.from ? n : D.cursor(r, r < n.from ? 1 : -1);
}
var fa = class {
	constructor(e, t) {
		this.pos = e, this.assoc = t;
	}
};
function pa(e, t, n, r) {
	let i = e.contentDOM.getBoundingClientRect(), a = i.top + e.viewState.paddingTop, { x: o, y: s } = t, c = s - a, l;
	for (;;) {
		if (c < 0) return new fa(0, 1);
		if (c > e.viewState.docHeight) return new fa(e.state.doc.length, -1);
		if (l = e.elementAtHeight(c), r == null) break;
		if (l.type == z.Text) {
			if (r < 0 ? l.to < e.viewport.from : l.from > e.viewport.to) break;
			let t = e.docView.coordsAt(r < 0 ? l.from : l.to, r > 0 ? -1 : 1);
			if (t && (r < 0 ? t.top <= c + a : t.bottom >= c + a)) break;
		}
		let t = e.viewState.heightOracle.textHeight / 2;
		c = r > 0 ? l.bottom + t : l.top - t;
	}
	if (e.viewport.from >= l.to || e.viewport.to <= l.from) {
		if (n) return null;
		if (l.type == z.Text) {
			let t = ra(e, i, l, o, s);
			return new fa(t, t == l.from ? 1 : -1);
		}
	}
	if (l.type != z.Text) return c < (l.top + l.bottom) / 2 ? new fa(l.from, 1) : new fa(l.to, -1);
	let u = e.docView.lineAt(l.from, 2);
	return (!u || u.length != l.length) && (u = e.docView.lineAt(l.from, -2)), new ma(e, o, s, e.textDirectionAt(l.from)).scanTile(u, l.from);
}
var ma = class {
	constructor(e, t, n, r) {
		this.view = e, this.x = t, this.y = n, this.baseDir = r, this.line = null, this.spans = null;
	}
	bidiSpansAt(e) {
		return (!this.line || this.line.from > e || this.line.to < e) && (this.line = this.view.state.doc.lineAt(e), this.spans = this.view.bidiSpans(this.line)), this;
	}
	baseDirAt(e, t) {
		let { line: n, spans: r } = this.bidiSpansAt(e);
		return r[Er.find(r, e - n.from, -1, t)].level == this.baseDir;
	}
	dirAt(e, t) {
		let { line: n, spans: r } = this.bidiSpansAt(e);
		return r[Er.find(r, e - n.from, -1, t)].dir;
	}
	bidiIn(e, t) {
		let { spans: n, line: r } = this.bidiSpansAt(e);
		return n.length > 1 || n.length && (n[0].level != this.baseDir || n[0].to + r.from < t);
	}
	scan(e, t, n = !1) {
		let r = 0, i = e.length - 1, a = /* @__PURE__ */ new Set(), o = this.bidiIn(e[0], e[i]), s, c, l = -1, u = 1e9, d;
		search: for (; r < i;) {
			let n = i - r, f = r + i >> 1;
			adjust: if (a.has(f)) {
				for (let e = 1; e < n; e++) {
					let t = f + e;
					if (t >= i && (t -= n), !a.has(t)) {
						f = t;
						break adjust;
					}
				}
				break search;
			}
			a.add(f);
			let p = t(f), m = 0;
			if (p) for (let e = 0; e < p.length; e++) {
				let t = p[e];
				if (!(t.width == 0 && p.length > 1)) {
					if (t.bottom < this.y) (!s || s.bottom < t.bottom) && (s = t), m = 1;
					else if (t.top > this.y) (!c || c.top > t.top) && (c = t), m = -1;
					else {
						let e = t.left > this.x ? this.x - t.left : t.right < this.x ? this.x - t.right : 0, n = Math.abs(e);
						n < u && (l = f, u = n, d = t), e && (m = e < 0 == (this.baseDir == V.LTR) ? -1 : 1);
					}
				}
			}
			m == -1 && (!o || this.baseDirAt(e[f], 1)) ? i = f : m == 1 && (!o || this.baseDirAt(e[f + 1], -1)) && (r = f + 1);
		}
		if (!d) {
			if (!c && !s) return {
				i: e[0],
				after: !1
			};
			let n = s && (!c || this.y - s.bottom < c.top - this.y) ? s : c;
			return this.y = (n.top + n.bottom) / 2, this.scan(e, t, !0);
		}
		if (u && !n) {
			let { top: n, bottom: r } = d;
			if (s && s.bottom > (n + n + r) / 3) return this.y = s.bottom - 1, this.scan(e, t, !0);
			if (c && c.top < (n + r + r) / 3) return this.y = c.top + 1, this.scan(e, t, !0);
		}
		let f = (o ? this.dirAt(e[l], 1) : this.baseDir) == V.LTR;
		return {
			i: l,
			after: this.x > (d.left + d.right) / 2 == f
		};
	}
	scanText(e, t) {
		let n = [];
		for (let r = 0; r < e.length; r = w(e.text, r)) n.push(t + r);
		n.push(t + e.length);
		let r = this.scan(n, (r) => {
			let i = n[r] - t, a = n[r + 1] - t;
			return lr(e.dom, i, a).getClientRects();
		});
		return r.after ? new fa(n[r.i + 1], -1) : new fa(n[r.i], 1);
	}
	scanTile(e, t) {
		if (!e.length) return new fa(t, 1);
		if (e.children.length == 1) {
			let n = e.children[0];
			if (n.isText()) return this.scanText(n, t);
			if (n.isComposite()) return this.scanTile(n, t);
		}
		let n = [t];
		for (let r = 0, i = t; r < e.children.length; r++) n.push(i += e.children[r].length);
		let r = this.scan(n, (t) => {
			let n = e.children[t];
			return n.flags & 48 ? null : (n.dom.nodeType == 1 ? n.dom : lr(n.dom, 0, n.length)).getClientRects();
		}), i = e.children[r.i], a = n[r.i];
		return i.isText() ? this.scanText(i, a) : i.isComposite() ? this.scanTile(i, a) : r.after ? new fa(n[r.i + 1], -1) : new fa(a, 1);
	}
}, ha = "￿", ga = class {
	constructor(e, t) {
		this.points = e, this.view = t, this.text = "", this.lineSeparator = t.state.facet(N.lineSeparator);
	}
	append(e) {
		this.text += e;
	}
	lineBreak() {
		this.text += ha;
	}
	readRange(e, t) {
		if (!e) return this;
		let n = e.parentNode;
		for (let r = e;;) {
			this.findPointBefore(n, r);
			let e = this.text.length;
			this.readNode(r);
			let i = G.get(r), a = r.nextSibling;
			if (a == t) {
				i != null && i.breakAfter && !a && n != this.view.contentDOM && this.lineBreak();
				break;
			}
			let o = G.get(a);
			(i && o ? i.breakAfter : (i ? i.breakAfter : Yn(r)) || Yn(a) && (r.nodeName != "BR" || i != null && i.isWidget()) && this.text.length > e) && !va(a, t) && this.lineBreak(), r = a;
		}
		return this.findPointBefore(n, t), this;
	}
	readTextNode(e) {
		let t = e.nodeValue;
		for (let n of this.points) n.node == e && (n.pos = this.text.length + Math.min(n.offset, t.length));
		for (let n = 0, r = this.lineSeparator ? null : /\r\n?|\n/g;;) {
			let i = -1, a = 1, o;
			if (this.lineSeparator ? (i = t.indexOf(this.lineSeparator, n), a = this.lineSeparator.length) : (o = r.exec(t)) && (i = o.index, a = o[0].length), this.append(t.slice(n, i < 0 ? t.length : i)), i < 0) break;
			if (this.lineBreak(), a > 1) for (let t of this.points) t.node == e && t.pos > this.text.length && (t.pos -= a - 1);
			n = i + a;
		}
	}
	readNode(e) {
		let t = G.get(e), n = t && t.overrideDOMText;
		if (n != null) {
			this.findPointInside(e, n.length);
			for (let e = n.iter(); !e.next().done;) e.lineBreak ? this.lineBreak() : this.append(e.value);
		} else e.nodeType == 3 ? this.readTextNode(e) : e.nodeName == "BR" ? e.nextSibling && this.lineBreak() : e.nodeType == 1 && this.readRange(e.firstChild, null);
	}
	findPointBefore(e, t) {
		for (let n of this.points) n.node == e && e.childNodes[n.offset] == t && (n.pos = this.text.length);
	}
	findPointInside(e, t) {
		for (let n of this.points) (e.nodeType == 3 ? n.node == e : e.contains(n.node)) && (n.pos = this.text.length + (_a(e, n.node, n.offset) ? t : 0));
	}
};
function _a(e, t, n) {
	for (;;) {
		if (!t || n < Zn(t)) return !1;
		if (t == e) return !0;
		n = Jn(t) + 1, t = t.parentNode;
	}
}
function va(e, t) {
	let n;
	for (; !(e == t || !e); e = e.nextSibling) {
		let t = G.get(e);
		if (!(t != null && t.isWidget())) return !1;
		t && (n || (n = [])).push(t);
	}
	if (n) for (let e of n) {
		let t = e.overrideDOMText;
		if (t != null && t.length) return !1;
	}
	return !0;
}
var ya = class {
	constructor(e, t) {
		this.node = e, this.offset = t, this.pos = -1;
	}
}, ba = class {
	constructor(e, t, n, r) {
		this.typeOver = r, this.bounds = null, this.text = "", this.domChanged = t > -1;
		let { impreciseHead: i, impreciseAnchor: a } = e.docView, o = e.state.selection;
		if (e.state.readOnly && t > -1) this.newSel = null;
		else if (t > -1 && (this.bounds = xa(e.docView.tile, t, n, 0))) {
			let t = i || a ? [] : Ea(e), n = new ga(t, e);
			n.readRange(this.bounds.startDOM, this.bounds.endDOM), this.text = n.text, this.newSel = Da(t, this.bounds.from);
		} else {
			let t = e.observer.selectionRange, n = i && i.node == t.focusNode && i.offset == t.focusOffset || !Wn(e.contentDOM, t.focusNode) ? o.main.head : e.docView.posFromDOM(t.focusNode, t.focusOffset), r = a && a.node == t.anchorNode && a.offset == t.anchorOffset || !Wn(e.contentDOM, t.anchorNode) ? o.main.anchor : e.docView.posFromDOM(t.anchorNode, t.anchorOffset), s = e.viewport;
			if ((R.ios || R.chrome) && n != r && Math.min(n, r) <= o.main.from && Math.max(n, r) >= o.main.to && (s.from > 0 || s.to < e.state.doc.length)) {
				let t = Math.min(n, r), i = Math.max(n, r), a = s.from - t, o = s.to - i;
				(a == 0 || a == 1 || t == 0) && (o == 0 || o == -1 || i == e.state.doc.length) && (n = 0, r = e.state.doc.length);
			}
			if (e.inputState.composing > -1 && o.ranges.length > 1) this.newSel = o.replaceRange(D.range(r, n));
			else if (e.lineWrapping && r == n && !(o.main.empty && o.main.head == n) && e.inputState.lastTouchTime > Date.now() - 100) {
				let t = e.coordsAtPos(n, -1), r = 0;
				t && (r = e.inputState.lastTouchY <= t.bottom ? -1 : 1), this.newSel = D.create([D.cursor(n, r)]);
			} else this.newSel = D.single(r, n);
		}
	}
};
function xa(e, t, n, r) {
	if (e.isComposite()) {
		let i = -1, a = -1, o = -1, s = -1;
		for (let c = 0, l = r, u = r; c < e.children.length; c++) {
			let r = e.children[c], d = l + r.length;
			if (l < t && d > n) return xa(r, t, n, l);
			if (d >= t && i == -1 && (i = c, a = l), l > n && r.dom.parentNode == e.dom) {
				o = c, s = u;
				break;
			}
			u = d, l = d + r.breakAfter;
		}
		return {
			from: a,
			to: s < 0 ? r + e.length : s,
			startDOM: (i ? e.children[i - 1].dom.nextSibling : null) || e.dom.firstChild,
			endDOM: o < e.children.length && o >= 0 ? e.children[o].dom : null
		};
	}
	return e.isText() ? {
		from: r,
		to: r + e.length,
		startDOM: e.dom,
		endDOM: e.dom.nextSibling
	} : null;
}
function Sa(e, t) {
	let n, { newSel: r } = t, { state: i } = e, a = i.selection.main, o = e.inputState.lastKeyTime > Date.now() - 100 ? e.inputState.lastKeyCode : -1;
	if (t.bounds) {
		let { from: e, to: r } = t.bounds, s = a.from, c = null;
		(o === 8 || R.android && t.text.length < r - e) && (s = a.to, c = "end");
		let l = i.doc.sliceString(e, r, ha), u, d;
		!a.empty && a.from >= e && a.to <= r && (t.typeOver || l != t.text) && l.slice(0, a.from - e) == t.text.slice(0, a.from - e) && l.slice(a.to - e) == t.text.slice(u = t.text.length - (l.length - (a.to - e))) ? n = {
			from: a.from,
			to: a.to,
			insert: C.of(t.text.slice(a.from - e, u).split(ha))
		} : (d = Ta(l, t.text, s - e, c)) && (R.chrome && o == 13 && d.toB == d.from + 2 && t.text.slice(d.from, d.toB) == "￿￿" && d.toB--, n = {
			from: e + d.from,
			to: e + d.toA,
			insert: C.of(t.text.slice(d.from, d.toB).split(ha))
		});
	} else r && (!e.hasFocus && i.facet($r) || Oa(r, a)) && (r = null);
	if (!n && !r) return !1;
	if ((R.mac || R.android) && n && n.from == n.to && n.from == a.head - 1 && /^\. ?$/.test(n.insert.toString()) && e.contentDOM.getAttribute("autocorrect") == "off" ? (r && n.insert.length == 2 && (r = D.single(r.main.anchor - 1, r.main.head - 1)), n = {
		from: n.from,
		to: n.to,
		insert: C.of([n.insert.toString().replace(".", " ")])
	}) : i.doc.lineAt(a.from).to < a.to && e.docView.lineHasWidget(a.to) && e.inputState.insertingTextAt > Date.now() - 50 ? n = {
		from: a.from,
		to: a.to,
		insert: i.toText(e.inputState.insertingText)
	} : R.chrome && n && n.from == n.to && n.from == a.head && n.insert.toString() == "\n " && e.lineWrapping && (r && (r = D.single(r.main.anchor - 1, r.main.head - 1)), n = {
		from: a.from,
		to: a.to,
		insert: C.of([" "])
	}), n) return Ca(e, n, r, o);
	if (r && !Oa(r, a)) {
		let t = !1, n = "select";
		return e.inputState.lastSelectionTime > Date.now() - 50 && (e.inputState.lastSelectionOrigin == "select" && (t = !0), n = e.inputState.lastSelectionOrigin, n == "select.pointer" && (r = ua(i.facet(ci).map((t) => t(e)), r))), e.dispatch({
			selection: r,
			scrollIntoView: t,
			userEvent: n
		}), !0;
	}
	return !1;
}
function Ca(e, t, n, r = -1) {
	if (R.ios && e.inputState.flushIOSKey(t)) return !0;
	let i = e.state.selection.main;
	if (R.android && (t.to == i.to && (t.from == i.from || t.from == i.from - 1 && e.state.sliceDoc(t.from, i.from) == " ") && t.insert.length == 1 && t.insert.lines == 2 && ur(e.contentDOM, "Enter", 13) || (t.from == i.from - 1 && t.to == i.to && t.insert.length == 0 || r == 8 && t.insert.length < t.to - t.from && t.to > i.head) && ur(e.contentDOM, "Backspace", 8) || t.from == i.from && t.to == i.to + 1 && t.insert.length == 0 && ur(e.contentDOM, "Delete", 46))) return !0;
	let a = t.insert.toString();
	e.inputState.composing >= 0 && e.inputState.composing++;
	let o, s = () => o || (o = wa(e, t, n));
	return e.state.facet(Ur).some((n) => n(e, t.from, t.to, a, s)) || e.dispatch(s()), !0;
}
function wa(e, t, n) {
	let r, i = e.state, a = i.selection.main, o = -1;
	if (t.from == t.to && t.from < a.from || t.from > a.to) {
		let n = t.from < a.from ? -1 : 1, r = n < 0 ? a.from : a.to, s = la(i.facet(ci).map((t) => t(e)), r, n);
		t.from == s && (o = s);
	}
	if (o > -1) r = {
		changes: t,
		selection: D.cursor(t.from + t.insert.length, -1)
	};
	else if (t.from >= a.from && t.to <= a.to && t.to - t.from >= (a.to - a.from) / 3 && (!n || n.main.empty && n.main.from == t.from + t.insert.length) && e.inputState.composing < 0) {
		let n = a.from < t.from ? i.sliceDoc(a.from, t.from) : "", o = a.to > t.to ? i.sliceDoc(t.to, a.to) : "";
		r = i.replaceSelection(e.state.toText(n + t.insert.sliceString(0, void 0, e.state.lineBreak) + o));
	} else {
		let o = i.changes(t), s = n && n.main.to <= o.newLength ? n.main : void 0;
		if (i.selection.ranges.length > 1 && (e.inputState.composing >= 0 || e.inputState.compositionPendingChange) && t.to <= a.to + 10 && t.to >= a.to - 10) {
			let c = e.state.sliceDoc(t.from, t.to), l, u = n && Ki(e, n.main.head);
			if (u) {
				let e = t.insert.length - (t.to - t.from);
				l = {
					from: u.from,
					to: u.to - e
				};
			} else l = e.state.doc.lineAt(a.head);
			let d = a.to - t.to;
			r = i.changeByRange((n) => {
				if (n.from == a.from && n.to == a.to) return {
					changes: o,
					range: s || n.map(o)
				};
				let r = n.to - d, u = r - c.length;
				if (e.state.sliceDoc(u, r) != c || r >= l.from && u <= l.to) return { range: n };
				let f = i.changes({
					from: u,
					to: r,
					insert: t.insert
				}), p = n.to - a.to;
				return {
					changes: f,
					range: s ? D.range(Math.max(0, s.anchor + p), Math.max(0, s.head + p)) : n.map(f)
				};
			});
		} else r = {
			changes: o,
			selection: s && i.selection.replaceRange(s)
		};
	}
	let s = "input.type";
	return (e.composing || e.inputState.compositionPendingChange && e.inputState.compositionEndedAt > Date.now() - 50) && (e.inputState.compositionPendingChange = !1, s += ".compose", e.inputState.compositionFirstChange && (s += ".start", e.inputState.compositionFirstChange = !1)), i.update(r, {
		userEvent: s,
		scrollIntoView: !0
	});
}
function Ta(e, t, n, r) {
	let i = Math.min(e.length, t.length), a = 0;
	for (; a < i && e.charCodeAt(a) == t.charCodeAt(a);) a++;
	if (a == i && e.length == t.length) return null;
	let o = e.length, s = t.length;
	for (; o > 0 && s > 0 && e.charCodeAt(o - 1) == t.charCodeAt(s - 1);) o--, s--;
	if (r == "end") {
		let e = Math.max(0, a - Math.min(o, s));
		n -= o + e - a;
	}
	if (o < a && e.length < t.length) {
		let e = n <= a && n >= o ? a - n : 0;
		a -= e, s = a + (s - o), o = a;
	} else if (s < a) {
		let e = n <= a && n >= s ? a - n : 0;
		a -= e, o = a + (o - s), s = a;
	}
	return {
		from: a,
		toA: o,
		toB: s
	};
}
function Ea(e) {
	let t = [];
	if (e.root.activeElement != e.contentDOM) return t;
	let { anchorNode: n, anchorOffset: r, focusNode: i, focusOffset: a } = e.observer.selectionRange;
	return n && (t.push(new ya(n, r)), (i != n || a != r) && t.push(new ya(i, a))), t;
}
function Da(e, t) {
	if (e.length == 0) return null;
	let n = e[0].pos, r = e.length == 2 ? e[1].pos : n;
	return n > -1 && r > -1 ? D.single(n + t, r + t) : null;
}
function Oa(e, t) {
	return t.head == e.main.head && t.anchor == e.main.anchor;
}
var ka = class {
	setSelectionOrigin(e) {
		this.lastSelectionOrigin = e, this.lastSelectionTime = Date.now();
	}
	constructor(e) {
		this.view = e, this.lastKeyCode = 0, this.lastKeyTime = 0, this.touchActive = !1, this.lastTouchTime = 0, this.lastTouchX = 0, this.lastTouchY = 0, this.lastFocusTime = 0, this.lastScrollTop = 0, this.lastScrollLeft = 0, this.lastWheelEvent = 0, this.pendingIOSKey = void 0, this.lastIOSMomentumScroll = 0, this.tabFocusMode = -1, this.lastSelectionOrigin = null, this.lastSelectionTime = 0, this.lastContextMenu = 0, this.scrollHandlers = [], this.handlers = Object.create(null), this.composing = -1, this.compositionFirstChange = null, this.compositionEndedAt = 0, this.compositionPendingKey = !1, this.compositionPendingChange = !1, this.insertingText = "", this.insertingTextAt = 0, this.mouseSelection = null, this.draggedContent = null, this.handleEvent = this.handleEvent.bind(this), this.notifiedFocused = e.hasFocus, R.safari && e.contentDOM.addEventListener("input", () => null), R.gecko && fo(e.contentDOM.ownerDocument);
	}
	handleEvent(e) {
		!Ua(this.view, e) || this.ignoreDuringComposition(e) || e.type == "keydown" && this.keydown(e) || (this.view.updateState == 0 ? this.runHandlers(e.type, e) : Promise.resolve().then(() => this.runHandlers(e.type, e)));
	}
	runHandlers(e, t) {
		let n = this.handlers[e];
		if (n) {
			for (let e of n.observers) e(this.view, t);
			for (let e of n.handlers) {
				if (t.defaultPrevented) break;
				if (e(this.view, t)) {
					t.preventDefault();
					break;
				}
			}
		}
	}
	ensureHandlers(e) {
		let t = Ma(e), n = this.handlers, r = this.view.contentDOM;
		for (let e in t) if (e != "scroll") {
			let i = !t[e].handlers.length, a = n[e];
			a && i != !a.handlers.length && (r.removeEventListener(e, this.handleEvent), a = null), a || r.addEventListener(e, this.handleEvent, { passive: i });
		}
		for (let e in n) e != "scroll" && !t[e] && r.removeEventListener(e, this.handleEvent);
		this.handlers = t;
	}
	keydown(e) {
		if (this.lastKeyCode = e.keyCode, this.lastKeyTime = Date.now(), e.keyCode == 9 && this.tabFocusMode > -1 && (!this.tabFocusMode || Date.now() <= this.tabFocusMode)) return !0;
		if (this.tabFocusMode > 0 && e.keyCode != 27 && Fa.indexOf(e.keyCode) < 0 && (this.tabFocusMode = -1), R.android && R.chrome && !e.synthetic && (e.keyCode == 13 || e.keyCode == 8)) return this.view.observer.delayAndroidKey(e.key, e.keyCode), !0;
		if (R.ios && !e.synthetic && !e.altKey && !e.metaKey && (Na.some((t) => t.keyCode == e.keyCode) && !e.ctrlKey || Pa.indexOf(e.key) > -1 && e.ctrlKey)) {
			let t = {
				ctrlKey: e.ctrlKey,
				altKey: e.altKey,
				metaKey: e.metaKey,
				shiftKey: e.shiftKey
			};
			return t.shiftKey && R.ios && !/^(off|none)$/.test(this.view.contentDOM.autocapitalize) && Aa(this.view.win) && (t.shiftKey = !1), this.pendingIOSKey = {
				key: e.key,
				keyCode: e.keyCode,
				mods: t
			}, setTimeout(() => this.flushIOSKey(), 250), !0;
		}
		return e.keyCode != 229 && this.view.observer.forceFlush(), !1;
	}
	flushIOSKey(e) {
		let t = this.pendingIOSKey;
		return !t || t.key == "Enter" && e && e.from < e.to && /^\S+$/.test(e.insert.toString()) ? !1 : (this.pendingIOSKey = void 0, ur(this.view.contentDOM, t.key, t.keyCode, t.mods));
	}
	ignoreDuringComposition(e) {
		return !/^key/.test(e.type) || e.synthetic ? !1 : this.composing > 0 ? !0 : R.safari && !R.ios && this.compositionPendingKey && Date.now() - this.compositionEndedAt < 100 ? (this.compositionPendingKey = !1, !0) : !1;
	}
	startMouseSelection(e) {
		this.mouseSelection && this.mouseSelection.destroy(), this.mouseSelection = e;
	}
	update(e) {
		this.view.observer.update(e), this.mouseSelection && this.mouseSelection.update(e), this.draggedContent && e.docChanged && (this.draggedContent = this.draggedContent.map(e.changes)), e.transactions.length && (this.lastKeyCode = this.lastSelectionTime = 0);
	}
	destroy() {
		this.mouseSelection && this.mouseSelection.destroy();
	}
};
function Aa(e) {
	return e.visualViewport ? e.visualViewport.height * e.visualViewport.scale / e.document.documentElement.clientHeight < .85 : !1;
}
function ja(e, t) {
	return (n, r) => {
		try {
			return t.call(e, r, n);
		} catch (e) {
			U(n.state, e);
		}
	};
}
function Ma(e) {
	let t = Object.create(null);
	function n(e) {
		return t[e] || (t[e] = {
			observers: [],
			handlers: []
		});
	}
	for (let t of e) {
		let e = t.spec, r = e && e.plugin.domEventHandlers, i = e && e.plugin.domEventObservers;
		if (r) for (let e in r) {
			let i = r[e];
			i && n(e).handlers.push(ja(t.value, i));
		}
		if (i) for (let e in i) {
			let r = i[e];
			r && n(e).observers.push(ja(t.value, r));
		}
	}
	for (let e in Wa) n(e).handlers.push(Wa[e]);
	for (let e in K) n(e).observers.push(K[e]);
	return t;
}
var Na = [
	{
		key: "Backspace",
		keyCode: 8,
		inputType: "deleteContentBackward"
	},
	{
		key: "Enter",
		keyCode: 13,
		inputType: "insertParagraph"
	},
	{
		key: "Enter",
		keyCode: 13,
		inputType: "insertLineBreak"
	},
	{
		key: "Delete",
		keyCode: 46,
		inputType: "deleteContentForward"
	}
], Pa = "dthko", Fa = [
	16,
	17,
	18,
	20,
	91,
	92,
	224,
	225
], Ia = 6;
function La(e) {
	return Math.max(0, e) * .7 + 8;
}
function Ra(e, t) {
	return Math.max(Math.abs(e.clientX - t.clientX), Math.abs(e.clientY - t.clientY));
}
var za = class {
	constructor(e, t, n, r) {
		this.view = e, this.startEvent = t, this.style = n, this.mustSelect = r, this.scrollSpeed = {
			x: 0,
			y: 0
		}, this.scrolling = -1, this.lastEvent = t, this.scrollParents = nr(e.contentDOM), this.atoms = e.state.facet(ci).map((t) => t(e));
		let i = e.contentDOM.ownerDocument;
		i.addEventListener("mousemove", this.move = this.move.bind(this)), i.addEventListener("mouseup", this.up = this.up.bind(this)), this.extend = t.shiftKey, this.multiple = e.state.facet(N.allowMultipleSelections) && Ba(e, t), this.dragging = Ha(e, t) && eo(t) == 1 ? null : !1;
	}
	start(e) {
		this.dragging === !1 && this.select(e);
	}
	move(e) {
		if (e.buttons == 0) return this.destroy();
		if (this.dragging || this.dragging == null && Ra(this.startEvent, e) < 10) return;
		this.select(this.lastEvent = e);
		let t = 0, n = 0, r = 0, i = 0, a = this.view.win.innerWidth, o = this.view.win.innerHeight;
		this.scrollParents.x && ({left: r, right: a} = this.scrollParents.x.getBoundingClientRect()), this.scrollParents.y && ({top: i, bottom: o} = this.scrollParents.y.getBoundingClientRect());
		let s = fi(this.view);
		e.clientX - s.left <= r + Ia ? t = -La(r - e.clientX) : e.clientX + s.right >= a - Ia && (t = La(e.clientX - a)), e.clientY - s.top <= i + Ia ? n = -La(i - e.clientY) : e.clientY + s.bottom >= o - Ia && (n = La(e.clientY - o)), this.setScrollSpeed(t, n);
	}
	up(e) {
		this.dragging == null && this.select(this.lastEvent), this.dragging || e.preventDefault(), this.destroy();
	}
	destroy() {
		this.setScrollSpeed(0, 0);
		let e = this.view.contentDOM.ownerDocument;
		e.removeEventListener("mousemove", this.move), e.removeEventListener("mouseup", this.up), this.view.inputState.mouseSelection = this.view.inputState.draggedContent = null;
	}
	setScrollSpeed(e, t) {
		this.scrollSpeed = {
			x: e,
			y: t
		}, e || t ? this.scrolling < 0 && (this.scrolling = setInterval(() => this.scroll(), 50)) : this.scrolling > -1 && (clearInterval(this.scrolling), this.scrolling = -1);
	}
	scroll() {
		let { x: e, y: t } = this.scrollSpeed;
		e && this.scrollParents.x && (this.scrollParents.x.scrollLeft += e, e = 0), t && this.scrollParents.y && (this.scrollParents.y.scrollTop += t, t = 0), (e || t) && this.view.win.scrollBy(e, t), this.dragging === !1 && this.select(this.lastEvent);
	}
	select(e) {
		let { view: t } = this, n = ua(this.atoms, this.style.get(e, this.extend, this.multiple));
		(this.mustSelect || !n.eq(t.state.selection, this.dragging === !1)) && this.view.dispatch({
			selection: n,
			userEvent: "select.pointer"
		}), this.mustSelect = !1;
	}
	update(e) {
		e.transactions.some((e) => e.isUserEvent("input.type")) ? this.destroy() : this.style.update(e) && setTimeout(() => this.select(this.lastEvent), 20);
	}
};
function Ba(e, t) {
	let n = e.state.facet(Rr);
	return n.length ? n[0](t) : R.mac ? t.metaKey : t.ctrlKey;
}
function Va(e, t) {
	let n = e.state.facet(zr);
	return n.length ? n[0](t) : R.mac ? !t.altKey : !t.ctrlKey;
}
function Ha(e, t) {
	let { main: n } = e.state.selection;
	if (n.empty) return !1;
	let r = Un(e.root);
	if (!r || r.rangeCount == 0) return !0;
	let i = r.getRangeAt(0).getClientRects();
	for (let e = 0; e < i.length; e++) {
		let n = i[e];
		if (n.left <= t.clientX && n.right >= t.clientX && n.top <= t.clientY && n.bottom >= t.clientY) return !0;
	}
	return !1;
}
function Ua(e, t) {
	if (!t.bubbles) return !0;
	if (t.defaultPrevented) return !1;
	for (let n = t.target, r; n != e.contentDOM; n = n.parentNode) if (!n || n.nodeType == 11 || (r = G.get(n)) && r.isWidget() && !r.isHidden && r.widget.ignoreEvent(t)) return !1;
	return !0;
}
var Wa = /*@__PURE__*/ Object.create(null), K = /*@__PURE__*/ Object.create(null), Ga = R.ie && R.ie_version < 15 || R.ios && R.webkit_version < 604;
function Ka(e) {
	let t = e.dom.parentNode;
	if (!t) return;
	let n = t.appendChild(document.createElement("textarea"));
	n.style.cssText = "position: fixed; left: -10000px; top: 10px", n.focus(), setTimeout(() => {
		e.focus(), n.remove(), Ja(e, n.value);
	}, 50);
}
function qa(e, t, n) {
	for (let r of e.facet(t)) n = r(n, e);
	return n;
}
function Ja(e, t) {
	t = qa(e.state, Gr, t);
	let { state: n } = e, r, i = 1, a = n.toText(t), o = a.lines == n.selection.ranges.length;
	if (oo != null && n.selection.ranges.every((e) => e.empty) && oo == a.toString()) {
		let e = -1;
		r = n.changeByRange((r) => {
			let s = n.doc.lineAt(r.from);
			if (s.from == e) return { range: r };
			e = s.from;
			let c = n.toText((o ? a.line(i++).text : t) + n.lineBreak);
			return {
				changes: {
					from: s.from,
					insert: c
				},
				range: D.cursor(r.from + c.length)
			};
		});
	} else r = o ? n.changeByRange((e) => {
		let t = a.line(i++);
		return {
			changes: {
				from: e.from,
				to: e.to,
				insert: t.text
			},
			range: D.cursor(e.from + t.length)
		};
	}) : n.replaceSelection(a);
	e.dispatch(r, {
		userEvent: "input.paste",
		scrollIntoView: !0
	});
}
K.scroll = (e) => {
	let t = e.inputState;
	t.lastScrollTop = e.scrollDOM.scrollTop, t.lastScrollLeft = e.scrollDOM.scrollLeft, R.ios && !t.touchActive && (t.lastIOSMomentumScroll = Date.now());
}, K.wheel = K.mousewheel = (e) => {
	e.inputState.lastWheelEvent = Date.now();
}, Wa.keydown = (e, t) => (e.inputState.setSelectionOrigin("select"), t.keyCode == 27 && e.inputState.tabFocusMode != 0 && (e.inputState.tabFocusMode = Date.now() + 2e3), !1), K.touchstart = (e, t) => {
	let n = e.inputState, r = t.targetTouches[0];
	n.touchActive = !0, n.lastTouchTime = Date.now(), r && (n.lastTouchX = r.clientX, n.lastTouchY = r.clientY), n.setSelectionOrigin("select.pointer");
}, K.touchmove = (e) => {
	e.inputState.setSelectionOrigin("select.pointer");
}, K.touchend = (e, t) => {
	e.inputState.touchActive = !1;
}, Wa.mousedown = (e, t) => {
	if (e.observer.flush(), e.inputState.lastTouchTime > Date.now() - 2e3) return !1;
	let n = null;
	for (let r of e.state.facet(Br)) if (n = r(e, t), n) break;
	if (!n && t.button == 0 && (n = to(e, t)), n) {
		let r = !e.hasFocus;
		e.inputState.startMouseSelection(new za(e, t, n, r)), r && e.observer.ignore(() => {
			sr(e.contentDOM);
			let t = e.root.activeElement;
			t && !t.contains(e.contentDOM) && t.blur();
		});
		let i = e.inputState.mouseSelection;
		if (i) return i.start(t), i.dragging === !1;
	} else e.inputState.setSelectionOrigin("select.pointer");
	return !1;
};
function Ya(e, t, n, r) {
	if (r == 1) return D.cursor(t, n);
	if (r == 2) return na(e.state, t, n);
	{
		let r = e.docView.lineAt(t, n), i = e.state.doc.lineAt(r ? r.posAtEnd : t), a = r ? r.posAtStart : i.from, o = r ? r.posAtEnd : i.to;
		return o < e.state.doc.length && o == i.to && o++, D.undirectionalRange(a, o);
	}
}
var Xa = R.ie && R.ie_version <= 11, Za = null, Qa = 0, $a = 0;
function eo(e) {
	if (!Xa) return e.detail;
	let t = Za, n = $a;
	return Za = e, $a = Date.now(), Qa = !t || n > Date.now() - 400 && Math.abs(t.clientX - e.clientX) < 2 && Math.abs(t.clientY - e.clientY) < 2 ? (Qa + 1) % 3 : 1;
}
function to(e, t) {
	let n = e.posAndSideAtCoords({
		x: t.clientX,
		y: t.clientY
	}, !1), r = eo(t), i = e.state.selection;
	return {
		update(e) {
			e.docChanged && (n.pos = e.changes.mapPos(n.pos), i = i.map(e.changes));
		},
		get(t, a, o) {
			let s = e.posAndSideAtCoords({
				x: t.clientX,
				y: t.clientY
			}, !1), c, l = Ya(e, s.pos, s.assoc, r);
			if (n.pos != s.pos && !a) {
				let t = Ya(e, n.pos, n.assoc, r), i = Math.min(t.from, l.from), a = Math.max(t.to, l.to);
				l = i < l.from ? D.range(i, a, l.assoc) : D.range(a, i, l.assoc);
			}
			return a ? i.replaceRange(i.main.extend(l.from, l.to, l.assoc)) : o && r == 1 && i.ranges.length > 1 && (c = no(i, s.pos)) ? c : o ? i.addRange(l) : D.create([l]);
		}
	};
}
function no(e, t) {
	for (let n = 0; n < e.ranges.length; n++) {
		let { from: r, to: i } = e.ranges[n];
		if (r <= t && i >= t) return D.create(e.ranges.slice(0, n).concat(e.ranges.slice(n + 1)), e.mainIndex == n ? 0 : e.mainIndex - +(e.mainIndex > n));
	}
	return null;
}
Wa.dragstart = (e, t) => {
	let { selection: { main: n } } = e.state;
	if (t.target.draggable) {
		let r = e.docView.tile.nearest(t.target);
		if (r && r.isWidget()) {
			let e = r.posAtStart, t = e + r.length;
			(e >= n.to || t <= n.from) && (n = D.undirectionalRange(e, t));
		}
	}
	let { inputState: r } = e;
	return r.mouseSelection && (r.mouseSelection.dragging = !0), r.draggedContent = n, t.dataTransfer && (t.dataTransfer.setData("Text", qa(e.state, Kr, e.state.sliceDoc(n.from, n.to))), t.dataTransfer.effectAllowed = "copyMove"), !1;
}, Wa.dragend = (e) => (e.inputState.draggedContent = null, !1);
function ro(e, t, n, r) {
	if (n = qa(e.state, Gr, n), !n) return;
	let i = e.posAtCoords({
		x: t.clientX,
		y: t.clientY
	}, !1), { draggedContent: a } = e.inputState, o = r && a && Va(e, t) ? {
		from: a.from,
		to: a.to
	} : null, s = {
		from: i,
		insert: n
	}, c = e.state.changes(o ? [o, s] : s);
	e.focus(), e.dispatch({
		changes: c,
		selection: {
			anchor: c.mapPos(i, -1),
			head: c.mapPos(i, 1)
		},
		userEvent: o ? "move.drop" : "input.drop"
	}), e.inputState.draggedContent = null;
}
Wa.drop = (e, t) => {
	if (!t.dataTransfer) return !1;
	if (e.state.readOnly) return !0;
	let n = t.dataTransfer.files;
	if (n && n.length) {
		let r = Array(n.length), i = 0, a = () => {
			++i == n.length && ro(e, t, r.filter((e) => e != null).join(e.state.lineBreak), !1);
		};
		for (let e = 0; e < n.length; e++) {
			let t = new FileReader();
			t.onerror = a, t.onload = () => {
				/[\x00-\x08\x0e-\x1f]{2}/.test(t.result) || (r[e] = t.result), a();
			}, t.readAsText(n[e]);
		}
		return !0;
	}
	{
		let n = t.dataTransfer.getData("Text");
		if (n) return ro(e, t, n, !0), !0;
	}
	return !1;
}, Wa.paste = (e, t) => {
	if (e.state.readOnly) return !0;
	e.observer.flush();
	let n = Ga ? null : t.clipboardData;
	return n ? (Ja(e, n.getData("text/plain") || n.getData("text/uri-list")), !0) : (Ka(e), !1);
};
function io(e, t) {
	let n = e.dom.parentNode;
	if (!n) return;
	let r = n.appendChild(document.createElement("textarea"));
	r.style.cssText = "position: fixed; left: -10000px; top: 10px", r.value = t, r.focus(), r.selectionEnd = t.length, r.selectionStart = 0, setTimeout(() => {
		r.remove(), e.focus();
	}, 50);
}
function ao(e) {
	let t = [], n = [], r = !1;
	for (let r of e.selection.ranges) r.empty || (t.push(e.sliceDoc(r.from, r.to)), n.push(r));
	if (!t.length) {
		let i = -1;
		for (let { from: r } of e.selection.ranges) {
			let a = e.doc.lineAt(r);
			a.number > i && (t.push(a.text), n.push({
				from: a.from,
				to: Math.min(e.doc.length, a.to + 1)
			})), i = a.number;
		}
		r = !0;
	}
	return {
		text: qa(e, Kr, t.join(e.lineBreak)),
		ranges: n,
		linewise: r
	};
}
var oo = null;
Wa.copy = Wa.cut = (e, t) => {
	if (!Gn(e.contentDOM, e.observer.selectionRange)) return !1;
	let { text: n, ranges: r, linewise: i } = ao(e.state);
	if (!n && !i) return !1;
	oo = i ? n : null, t.type == "cut" && !e.state.readOnly && e.dispatch({
		changes: r,
		scrollIntoView: !0,
		userEvent: "delete.cut"
	});
	let a = Ga ? null : t.clipboardData;
	return a ? (a.clearData(), a.setData("text/plain", n), !0) : (io(e, n), !1);
};
var so = /*@__PURE__*/ _t.define();
function co(e, t) {
	let n = [];
	for (let r of e.facet(Wr)) {
		let i = r(e, t);
		i && n.push(i);
	}
	return n.length ? e.update({
		effects: n,
		annotations: so.of(!0)
	}) : null;
}
function lo(e) {
	setTimeout(() => {
		let t = e.hasFocus;
		if (t != e.inputState.notifiedFocused) {
			let n = co(e.state, t);
			n ? e.dispatch(n) : e.update([]);
		}
	}, 10);
}
K.focus = (e) => {
	e.inputState.lastFocusTime = Date.now(), !e.scrollDOM.scrollTop && (e.inputState.lastScrollTop || e.inputState.lastScrollLeft) && (e.scrollDOM.scrollTop = e.inputState.lastScrollTop, e.scrollDOM.scrollLeft = e.inputState.lastScrollLeft), lo(e);
}, K.blur = (e) => {
	e.observer.clearSelectionRange(), lo(e);
}, K.compositionstart = K.compositionupdate = (e) => {
	e.observer.editContext || (e.inputState.compositionFirstChange == null && (e.inputState.compositionFirstChange = !0), e.inputState.composing < 0 && (e.inputState.composing = 0));
}, K.compositionend = (e) => {
	e.observer.editContext || (e.inputState.composing = -1, e.inputState.compositionEndedAt = Date.now(), e.inputState.compositionPendingKey = !0, e.inputState.compositionPendingChange = e.observer.pendingRecords().length > 0, e.inputState.compositionFirstChange = null, R.chrome && R.android ? e.observer.flushSoon() : e.inputState.compositionPendingChange ? Promise.resolve().then(() => e.observer.flush()) : setTimeout(() => {
		e.inputState.composing < 0 && e.docView.hasComposition && e.update([]);
	}, 50));
}, K.contextmenu = (e) => {
	e.inputState.lastContextMenu = Date.now();
}, Wa.beforeinput = (e, t) => {
	var n, r;
	if ((t.inputType == "insertText" || t.inputType == "insertCompositionText") && (e.inputState.insertingText = t.data, e.inputState.insertingTextAt = Date.now()), t.inputType == "insertReplacementText" && e.observer.editContext) {
		let r = (n = t.dataTransfer) == null ? void 0 : n.getData("text/plain"), i = t.getTargetRanges();
		if (r && i.length) {
			let t = i[0];
			return Ca(e, {
				from: e.posAtDOM(t.startContainer, t.startOffset),
				to: e.posAtDOM(t.endContainer, t.endOffset),
				insert: e.state.toText(r)
			}, null), !0;
		}
	}
	let i;
	if (R.chrome && R.android && (i = Na.find((e) => e.inputType == t.inputType)) && (e.observer.delayAndroidKey(i.key, i.keyCode), i.key == "Backspace" || i.key == "Delete")) {
		let t = ((r = window.visualViewport) == null ? void 0 : r.height) || 0;
		setTimeout(() => {
			var n;
			(((n = window.visualViewport) == null ? void 0 : n.height) || 0) > t + 10 && e.hasFocus && (e.contentDOM.blur(), e.focus());
		}, 100);
	}
	return R.ios && t.inputType == "deleteContentForward" && e.observer.flushSoon(), R.safari && t.inputType == "insertText" && e.inputState.composing >= 0 && setTimeout(() => K.compositionend(e, t), 20), !1;
};
var uo = /*@__PURE__*/ new Set();
function fo(e) {
	uo.has(e) || (uo.add(e), e.addEventListener("copy", () => {}), e.addEventListener("cut", () => {}));
}
var po = [
	"pre-wrap",
	"normal",
	"pre-line",
	"break-spaces"
], mo = !1;
function ho() {
	mo = !1;
}
var go = class {
	constructor(e) {
		this.lineWrapping = e, this.doc = C.empty, this.heightSamples = {}, this.lineHeight = 14, this.charWidth = 7, this.textHeight = 14, this.lineLength = 30;
	}
	heightForGap(e, t) {
		let n = this.doc.lineAt(t).number - this.doc.lineAt(e).number + 1;
		return this.lineWrapping && (n += Math.max(0, Math.ceil((t - e - n * this.lineLength * .5) / this.lineLength))), this.lineHeight * n;
	}
	heightForLine(e) {
		return this.lineWrapping ? (1 + Math.max(0, Math.ceil((e - this.lineLength) / Math.max(1, this.lineLength - 5)))) * this.lineHeight : this.lineHeight;
	}
	setDoc(e) {
		return this.doc = e, this;
	}
	mustRefreshForWrapping(e) {
		return po.indexOf(e) > -1 != this.lineWrapping;
	}
	mustRefreshForHeights(e) {
		let t = !1;
		for (let n = 0; n < e.length; n++) {
			let r = e[n];
			r < 0 ? n++ : this.heightSamples[Math.floor(r * 10)] || (t = !0, this.heightSamples[Math.floor(r * 10)] = !0);
		}
		return t;
	}
	refresh(e, t, n, r, i, a) {
		let o = po.indexOf(e) > -1, s = Math.abs(t - this.lineHeight) > .3 || this.lineWrapping != o;
		if (this.lineWrapping = o, this.lineHeight = t, this.charWidth = n, this.textHeight = r, this.lineLength = i, s) {
			this.heightSamples = {};
			for (let e = 0; e < a.length; e++) {
				let t = a[e];
				t < 0 ? e++ : this.heightSamples[Math.floor(t * 10)] = !0;
			}
		}
		return s;
	}
}, _o = class {
	constructor(e, t) {
		this.from = e, this.heights = t, this.index = 0;
	}
	get more() {
		return this.index < this.heights.length;
	}
}, vo = class e {
	constructor(e, t, n, r, i) {
		this.from = e, this.length = t, this.top = n, this.height = r, this._content = i;
	}
	get type() {
		return typeof this._content == "number" ? z.Text : Array.isArray(this._content) ? this._content : this._content.type;
	}
	get to() {
		return this.from + this.length;
	}
	get bottom() {
		return this.top + this.height;
	}
	get widget() {
		return this._content instanceof Rn ? this._content.widget : null;
	}
	get widgetLineBreaks() {
		return typeof this._content == "number" ? this._content : 0;
	}
	join(t) {
		let n = (Array.isArray(this._content) ? this._content : [this]).concat(Array.isArray(t._content) ? t._content : [t]);
		return new e(this.from, this.length + t.length, this.top, this.height + t.height, n);
	}
}, q = /*@__PURE__*/ (function(e) {
	return e[e.ByPos = 0] = "ByPos", e[e.ByHeight = 1] = "ByHeight", e[e.ByPosNoHeight = 2] = "ByPosNoHeight", e;
})(q || (q = {})), yo = .001, bo = class e {
	constructor(e, t, n = 2) {
		this.length = e, this.height = t, this.flags = n;
	}
	get outdated() {
		return (this.flags & 2) > 0;
	}
	set outdated(e) {
		this.flags = (e ? 2 : 0) | this.flags & -3;
	}
	setHeight(e) {
		this.height != e && (Math.abs(this.height - e) > yo && (mo = !0), this.height = e);
	}
	replace(t, n, r) {
		return e.of(r);
	}
	decomposeLeft(e, t) {
		t.push(this);
	}
	decomposeRight(e, t) {
		t.push(this);
	}
	applyChanges(e, t, n, r) {
		let i = this, a = n.doc;
		for (let o = r.length - 1; o >= 0; o--) {
			let { fromA: s, toA: c, fromB: l, toB: u } = r[o], d = i.lineAt(s, q.ByPosNoHeight, n.setDoc(t), 0, 0), f = d.to >= c ? d : i.lineAt(c, q.ByPosNoHeight, n, 0, 0);
			for (u += f.to - c, c = f.to; o > 0 && d.from <= r[o - 1].toA;) s = r[o - 1].fromA, l = r[o - 1].fromB, o--, s < d.from && (d = i.lineAt(s, q.ByPosNoHeight, n, 0, 0));
			l += d.from - s, s = d.from;
			let p = ko.build(n.setDoc(a), e, l, u);
			i = xo(i, i.replace(s, c, p));
		}
		return i.updateHeight(n, 0);
	}
	static empty() {
		return new wo(0, 0, 0);
	}
	static of(t) {
		if (t.length == 1) return t[0];
		let n = 0, r = t.length, i = 0, a = 0;
		for (;;) if (n == r) {
			if (i > a * 2) {
				let e = t[n - 1];
				e.break ? t.splice(--n, 1, e.left, null, e.right) : t.splice(--n, 1, e.left, e.right), r += 1 + e.break, i -= e.size;
			} else if (a > i * 2) {
				let e = t[r];
				e.break ? t.splice(r, 1, e.left, null, e.right) : t.splice(r, 1, e.left, e.right), r += 2 + e.break, a -= e.size;
			} else break;
		} else if (i < a) {
			let e = t[n++];
			e && (i += e.size);
		} else {
			let e = t[--r];
			e && (a += e.size);
		}
		let o = 0;
		return t[n - 1] == null ? (o = 1, n--) : t[n] == null && (o = 1, r++), new Eo(e.of(t.slice(0, n)), o, e.of(t.slice(r)));
	}
};
function xo(e, t) {
	return e == t ? e : (e.constructor != t.constructor && (mo = !0), t);
}
bo.prototype.size = 1;
var So = /*@__PURE__*/ B.replace({}), Co = class extends bo {
	constructor(e, t, n) {
		super(e, t), this.deco = n, this.spaceAbove = 0;
	}
	mainBlock(e, t) {
		return new vo(t, this.length, e + this.spaceAbove, this.height - this.spaceAbove, this.deco || 0);
	}
	blockAt(e, t, n, r) {
		return this.spaceAbove && e < n + this.spaceAbove ? new vo(r, 0, n, this.spaceAbove, So) : this.mainBlock(n, r);
	}
	lineAt(e, t, n, r, i) {
		let a = this.mainBlock(r, i);
		return this.spaceAbove ? this.blockAt(0, n, r, i).join(a) : a;
	}
	forEachLine(e, t, n, r, i, a) {
		e <= i + this.length && t >= i && a(this.lineAt(0, q.ByPos, n, r, i));
	}
	setMeasuredHeight(e) {
		let t = e.heights[e.index++];
		t < 0 ? (this.spaceAbove = -t, t = e.heights[e.index++]) : this.spaceAbove = 0, this.setHeight(t);
	}
	updateHeight(e, t = 0, n = !1, r) {
		return r && r.from <= t && r.more && this.setMeasuredHeight(r), this.outdated = !1, this;
	}
	toString() {
		return `block(${this.length})`;
	}
}, wo = class e extends Co {
	constructor(e, t, n) {
		super(e, t, null), this.collapsed = 0, this.widgetHeight = 0, this.breaks = 0, this.spaceAbove = n;
	}
	mainBlock(e, t) {
		return new vo(t, this.length, e + this.spaceAbove, this.height - this.spaceAbove, this.breaks);
	}
	replace(t, n, r) {
		let i = r[0];
		return r.length == 1 && (i instanceof e || i instanceof To && i.flags & 4) && Math.abs(this.length - i.length) < 10 ? (i instanceof To ? i = new e(i.length, this.height, this.spaceAbove) : i.height = this.height, this.outdated || (i.outdated = !1), i) : bo.of(r);
	}
	updateHeight(e, t = 0, n = !1, r) {
		return r && r.from <= t && r.more ? this.setMeasuredHeight(r) : (n || this.outdated) && (this.spaceAbove = 0, this.setHeight(Math.max(this.widgetHeight, e.heightForLine(this.length - this.collapsed)) + this.breaks * e.lineHeight)), this.outdated = !1, this;
	}
	toString() {
		return `line(${this.length}${this.collapsed ? -this.collapsed : ""}${this.widgetHeight ? ":" + this.widgetHeight : ""})`;
	}
}, To = class e extends bo {
	constructor(e) {
		super(e, 0);
	}
	heightMetrics(e, t) {
		let n = e.doc.lineAt(t).number, r = e.doc.lineAt(t + this.length).number, i = r - n + 1, a, o = 0;
		if (e.lineWrapping) {
			let t = Math.min(this.height, e.lineHeight * i);
			a = t / i, this.length > i + 1 && (o = (this.height - t) / (this.length - i - 1));
		} else a = this.height / i;
		return {
			firstLine: n,
			lastLine: r,
			perLine: a,
			perChar: o
		};
	}
	blockAt(e, t, n, r) {
		let { firstLine: i, lastLine: a, perLine: o, perChar: s } = this.heightMetrics(t, r);
		if (t.lineWrapping) {
			let i = r + (e < t.lineHeight ? 0 : Math.round(Math.max(0, Math.min(1, (e - n) / this.height)) * this.length)), a = t.doc.lineAt(i), c = o + a.length * s, l = Math.max(n, e - c / 2);
			return new vo(a.from, a.length, l, c, 0);
		}
		{
			let r = Math.max(0, Math.min(a - i, Math.floor((e - n) / o))), { from: s, length: c } = t.doc.line(i + r);
			return new vo(s, c, n + o * r, o, 0);
		}
	}
	lineAt(e, t, n, r, i) {
		if (t == q.ByHeight) return this.blockAt(e, n, r, i);
		if (t == q.ByPosNoHeight) {
			let { from: t, to: r } = n.doc.lineAt(e);
			return new vo(t, r - t, 0, 0, 0);
		}
		let { firstLine: a, perLine: o, perChar: s } = this.heightMetrics(n, i), c = n.doc.lineAt(e), l = o + c.length * s, u = c.number - a, d = r + o * u + s * (c.from - i - u);
		return new vo(c.from, c.length, Math.max(r, Math.min(d, r + this.height - l)), l, 0);
	}
	forEachLine(e, t, n, r, i, a) {
		e = Math.max(e, i), t = Math.min(t, i + this.length);
		let { firstLine: o, perLine: s, perChar: c } = this.heightMetrics(n, i);
		for (let l = e, u = r; l <= t;) {
			let t = n.doc.lineAt(l);
			if (l == e) {
				let n = t.number - o;
				u += s * n + c * (e - i - n);
			}
			let r = s + c * t.length;
			a(new vo(t.from, t.length, u, r, 0)), u += r, l = t.to + 1;
		}
	}
	replace(t, n, r) {
		let i = this.length - n;
		if (i > 0) {
			let t = r[r.length - 1];
			t instanceof e ? r[r.length - 1] = new e(t.length + i) : r.push(null, new e(i - 1));
		}
		if (t > 0) {
			let n = r[0];
			n instanceof e ? r[0] = new e(t + n.length) : r.unshift(new e(t - 1), null);
		}
		return bo.of(r);
	}
	decomposeLeft(t, n) {
		n.push(new e(t - 1), null);
	}
	decomposeRight(t, n) {
		n.push(null, new e(this.length - t - 1));
	}
	updateHeight(t, n = 0, r = !1, i) {
		let a = n + this.length;
		if (i && i.from <= n + this.length && i.more) {
			let r = [], o = Math.max(n, i.from), s = -1;
			for (i.from > n && r.push(new e(i.from - n - 1).updateHeight(t, n)); o <= a && i.more;) {
				let e = t.doc.lineAt(o).length;
				r.length && r.push(null);
				let n = i.heights[i.index++], a = 0;
				n < 0 && (a = -n, n = i.heights[i.index++]), s == -1 ? s = n : Math.abs(n - s) >= yo && (s = -2);
				let c = new wo(e, n, a);
				c.outdated = !1, r.push(c), o += e + 1;
			}
			o <= a && r.push(null, new e(a - o).updateHeight(t, o));
			let c = bo.of(r);
			return (s < 0 || Math.abs(c.height - this.height) >= yo || Math.abs(s - this.heightMetrics(t, n).perLine) >= yo) && (mo = !0), xo(this, c);
		}
		return (r || this.outdated) && (this.setHeight(t.heightForGap(n, n + this.length)), this.outdated = !1), this;
	}
	toString() {
		return `gap(${this.length})`;
	}
}, Eo = class extends bo {
	constructor(e, t, n) {
		super(e.length + t + n.length, e.height + n.height, t | (e.outdated || n.outdated ? 2 : 0)), this.left = e, this.right = n, this.size = e.size + n.size;
	}
	get break() {
		return this.flags & 1;
	}
	blockAt(e, t, n, r) {
		let i = n + this.left.height;
		return e < i ? this.left.blockAt(e, t, n, r) : this.right.blockAt(e, t, i, r + this.left.length + this.break);
	}
	lineAt(e, t, n, r, i) {
		let a = r + this.left.height, o = i + this.left.length + this.break, s = t == q.ByHeight ? e < a : e < o, c = s ? this.left.lineAt(e, t, n, r, i) : this.right.lineAt(e, t, n, a, o);
		if (this.break || (s ? c.to < o : c.from > o)) return c;
		let l = t == q.ByPosNoHeight ? q.ByPosNoHeight : q.ByPos;
		return s ? c.join(this.right.lineAt(o, l, n, a, o)) : this.left.lineAt(o, l, n, r, i).join(c);
	}
	forEachLine(e, t, n, r, i, a) {
		let o = r + this.left.height, s = i + this.left.length + this.break;
		if (this.break) e < s && this.left.forEachLine(e, t, n, r, i, a), t >= s && this.right.forEachLine(e, t, n, o, s, a);
		else {
			let c = this.lineAt(s, q.ByPos, n, r, i);
			e < c.from && this.left.forEachLine(e, c.from - 1, n, r, i, a), c.to >= e && c.from <= t && a(c), t > c.to && this.right.forEachLine(c.to + 1, t, n, o, s, a);
		}
	}
	replace(e, t, n) {
		let r = this.left.length + this.break;
		if (t < r) return this.balanced(this.left.replace(e, t, n), this.right);
		if (e > this.left.length) return this.balanced(this.left, this.right.replace(e - r, t - r, n));
		let i = [];
		e > 0 && this.decomposeLeft(e, i);
		let a = i.length;
		for (let e of n) i.push(e);
		if (e > 0 && Do(i, a - 1), t < this.length) {
			let e = i.length;
			this.decomposeRight(t, i), Do(i, e);
		}
		return bo.of(i);
	}
	decomposeLeft(e, t) {
		let n = this.left.length;
		if (e <= n) return this.left.decomposeLeft(e, t);
		t.push(this.left), this.break && (n++, e >= n && t.push(null)), e > n && this.right.decomposeLeft(e - n, t);
	}
	decomposeRight(e, t) {
		let n = this.left.length, r = n + this.break;
		if (e >= r) return this.right.decomposeRight(e - r, t);
		e < n && this.left.decomposeRight(e, t), this.break && e < r && t.push(null), t.push(this.right);
	}
	balanced(e, t) {
		return e.size > 2 * t.size || t.size > 2 * e.size ? bo.of(this.break ? [
			e,
			null,
			t
		] : [e, t]) : (this.left = xo(this.left, e), this.right = xo(this.right, t), this.setHeight(e.height + t.height), this.outdated = e.outdated || t.outdated, this.size = e.size + t.size, this.length = e.length + this.break + t.length, this);
	}
	updateHeight(e, t = 0, n = !1, r) {
		let { left: i, right: a } = this, o = t + i.length + this.break, s = null;
		return r && r.from <= t + i.length && r.more ? s = i = i.updateHeight(e, t, n, r) : i.updateHeight(e, t, n), r && r.from <= o + a.length && r.more ? s = a = a.updateHeight(e, o, n, r) : a.updateHeight(e, o, n), s ? this.balanced(i, a) : (this.height = this.left.height + this.right.height, this.outdated = !1, this);
	}
	toString() {
		return this.left + (this.break ? " " : "-") + this.right;
	}
};
function Do(e, t) {
	let n, r;
	e[t] == null && (n = e[t - 1]) instanceof To && (r = e[t + 1]) instanceof To && e.splice(t - 1, 3, new To(n.length + 1 + r.length));
}
var Oo = 5, ko = class e {
	constructor(e, t) {
		this.pos = e, this.oracle = t, this.nodes = [], this.lineStart = -1, this.lineEnd = -1, this.covering = null, this.writtenTo = e;
	}
	get isCovered() {
		return this.covering && this.nodes[this.nodes.length - 1] == this.covering;
	}
	span(e, t) {
		if (this.lineStart > -1) {
			let e = Math.min(t, this.lineEnd), n = this.nodes[this.nodes.length - 1];
			n instanceof wo ? n.length += e - this.pos : (e > this.pos || !this.isCovered) && this.nodes.push(new wo(e - this.pos, -1, 0)), this.writtenTo = e, t > e && (this.nodes.push(null), this.writtenTo++, this.lineStart = -1);
		}
		this.pos = t;
	}
	point(e, t, n) {
		if (e < t || n.heightRelevant) {
			let r = n.widget ? n.widget.estimatedHeight : 0, i = n.widget ? n.widget.lineBreaks : 0;
			r < 0 && (r = this.oracle.lineHeight);
			let a = t - e;
			n.block ? this.addBlock(new Co(a, r, n)) : (a || i || r >= Oo) && this.addLineDeco(r, i, a);
		} else t > e && this.span(e, t);
		this.lineEnd > -1 && this.lineEnd < this.pos && (this.lineEnd = this.oracle.doc.lineAt(this.pos).to);
	}
	enterLine() {
		if (this.lineStart > -1) return;
		let { from: e, to: t } = this.oracle.doc.lineAt(this.pos);
		this.lineStart = e, this.lineEnd = t, this.writtenTo < e && ((this.writtenTo < e - 1 || this.nodes[this.nodes.length - 1] == null) && this.nodes.push(this.blankContent(this.writtenTo, e - 1)), this.nodes.push(null)), this.pos > e && this.nodes.push(new wo(this.pos - e, -1, 0)), this.writtenTo = this.pos;
	}
	blankContent(e, t) {
		let n = new To(t - e);
		return this.oracle.doc.lineAt(e).to == t && (n.flags |= 4), n;
	}
	ensureLine() {
		this.enterLine();
		let e = this.nodes.length ? this.nodes[this.nodes.length - 1] : null;
		if (e instanceof wo) return e;
		let t = new wo(0, -1, 0);
		return this.nodes.push(t), t;
	}
	addBlock(e) {
		this.enterLine();
		let t = e.deco;
		t && t.startSide > 0 && !this.isCovered && this.ensureLine(), this.nodes.push(e), this.writtenTo = this.pos += e.length, t && t.endSide > 0 && (this.covering = e);
	}
	addLineDeco(e, t, n) {
		let r = this.ensureLine();
		r.length += n, r.collapsed += n, r.widgetHeight = Math.max(r.widgetHeight, e), r.breaks += t, this.writtenTo = this.pos += n;
	}
	finish(e) {
		let t = this.nodes.length == 0 ? null : this.nodes[this.nodes.length - 1];
		this.lineStart > -1 && !(t instanceof wo) && !this.isCovered ? this.nodes.push(new wo(0, -1, 0)) : (this.writtenTo < this.pos || t == null) && this.nodes.push(this.blankContent(this.writtenTo, this.pos));
		let n = e;
		for (let e of this.nodes) e instanceof wo && e.updateHeight(this.oracle, n), n += e ? e.length : 1;
		return this.nodes;
	}
	static build(t, n, r, i) {
		let a = new e(r, t);
		return P.spans(n, r, i, a, 0), a.finish(r);
	}
};
function Ao(e, t, n) {
	let r = new jo();
	return P.compare(e, t, n, r, 0), r.changes;
}
var jo = class {
	constructor() {
		this.changes = [];
	}
	compareRange() {}
	comparePoint(e, t, n, r) {
		(e < t || n && n.heightRelevant || r && r.heightRelevant) && Vn(e, t, this.changes, 5);
	}
};
function Mo(e, t) {
	let n = e.getBoundingClientRect(), r = e.ownerDocument, i = r.defaultView || window, a = Math.max(0, n.left), o = Math.min(i.innerWidth, n.right), s = Math.max(0, n.top), c = Math.min(i.innerHeight, n.bottom);
	for (let t = e.parentNode; t && t != r.body;) if (t.nodeType == 1) {
		let n = t, r = window.getComputedStyle(n);
		if ((n.scrollHeight > n.clientHeight || n.scrollWidth > n.clientWidth) && r.overflow != "visible") {
			let r = n.getBoundingClientRect();
			a = Math.max(a, r.left), o = Math.min(o, r.right), s = Math.max(s, r.top), c = Math.min(t == e.parentNode ? i.innerHeight : c, r.bottom);
		}
		t = r.position == "absolute" || r.position == "fixed" ? n.offsetParent : n.parentNode;
	} else if (t.nodeType == 11) t = t.host;
	else break;
	return {
		left: a - n.left,
		right: Math.max(a, o) - n.left,
		top: s - (n.top + t),
		bottom: Math.max(s, c) - (n.top + t)
	};
}
function No(e) {
	let t = e.getBoundingClientRect(), n = e.ownerDocument.defaultView || window;
	return t.left < n.innerWidth && t.right > 0 && t.top < n.innerHeight && t.bottom > 0;
}
function Po(e, t) {
	let n = e.getBoundingClientRect();
	return {
		left: 0,
		right: n.right - n.left,
		top: t,
		bottom: n.bottom - (n.top + t)
	};
}
var Fo = class {
	constructor(e, t, n, r) {
		this.from = e, this.to = t, this.size = n, this.displaySize = r;
	}
	static same(e, t) {
		if (e.length != t.length) return !1;
		for (let n = 0; n < e.length; n++) {
			let r = e[n], i = t[n];
			if (r.from != i.from || r.to != i.to || r.size != i.size) return !1;
		}
		return !0;
	}
	draw(e, t) {
		return B.replace({ widget: new Io(this.displaySize * (t ? e.scaleY : e.scaleX), t) }).range(this.from, this.to);
	}
}, Io = class extends Fn {
	constructor(e, t) {
		super(), this.size = e, this.vertical = t;
	}
	eq(e) {
		return e.size == this.size && e.vertical == this.vertical;
	}
	toDOM() {
		let e = document.createElement("div");
		return this.vertical ? e.style.height = this.size + "px" : (e.style.width = this.size + "px", e.style.height = "2px", e.style.display = "inline-block"), e;
	}
	get estimatedHeight() {
		return this.vertical ? this.size : -1;
	}
}, Lo = class {
	constructor(e, t) {
		this.view = e, this.state = t, this.pixelViewport = {
			left: 0,
			right: window.innerWidth,
			top: 0,
			bottom: 0
		}, this.inView = !0, this.paddingTop = 0, this.paddingBottom = 0, this.contentDOMWidth = 0, this.contentDOMHeight = 0, this.editorHeight = 0, this.editorWidth = 0, this.scaleX = 1, this.scaleY = 1, this.scrollOffset = 0, this.scrolledToBottom = !1, this.scrollAnchorPos = 0, this.scrollAnchorHeight = -1, this.scaler = Uo, this.scrollTarget = null, this.printing = !1, this.mustMeasureContent = !0, this.defaultTextDirection = V.LTR, this.visibleRanges = [], this.mustEnforceCursorAssoc = !1;
		let n = t.facet(ii).some((e) => typeof e != "function" && e.class == "cm-lineWrapping");
		this.heightOracle = new go(n), this.stateDeco = Wo(t), this.heightMap = bo.empty().applyChanges(this.stateDeco, C.empty, this.heightOracle.setDoc(t.doc), [new mi(0, 0, 0, t.doc.length)]);
		for (let e = 0; e < 2 && (this.viewport = this.getViewport(0, null), this.updateForViewport()); e++);
		this.updateViewportLines(), this.lineGaps = this.ensureLineGaps([]), this.lineGapDeco = B.set(this.lineGaps.map((e) => e.draw(this, !1))), this.scrollParent = e.scrollDOM, this.computeVisibleRanges();
	}
	updateForViewport() {
		let e = [this.viewport], { main: t } = this.state.selection;
		for (let n = 0; n <= 1; n++) {
			let r = n ? t.head : t.anchor;
			if (!e.some(({ from: e, to: t }) => r >= e && r <= t)) {
				let { from: t, to: n } = this.lineBlockAt(r);
				e.push(new Ro(t, n));
			}
		}
		return this.viewports = e.sort((e, t) => e.from - t.from), this.updateScaler();
	}
	updateScaler() {
		let e = this.scaler;
		return this.scaler = this.heightMap.height <= 7e6 ? Uo : new Go(this.heightOracle, this.heightMap, this.viewports), e.eq(this.scaler) ? 0 : 2;
	}
	updateViewportLines() {
		this.viewportLines = [], this.heightMap.forEachLine(this.viewport.from, this.viewport.to, this.heightOracle.setDoc(this.state.doc), 0, 0, (e) => {
			this.viewportLines.push(Ko(e, this.scaler));
		});
	}
	update(e, t = null) {
		this.state = e.state;
		let n = this.stateDeco;
		this.stateDeco = Wo(this.state);
		let r = e.changedRanges, i = mi.extendWithRanges(r, Ao(n, this.stateDeco, e ? e.changes : ze.empty(this.state.doc.length))), a = this.heightMap.height, o = this.scrolledToBottom ? null : this.scrollAnchorAt(this.scrollOffset);
		ho(), this.heightMap = this.heightMap.applyChanges(this.stateDeco, e.startState.doc, this.heightOracle.setDoc(this.state.doc), i), (this.heightMap.height != a || mo) && (e.flags |= 2), o ? (this.scrollAnchorPos = e.changes.mapPos(o.from, -1), this.scrollAnchorHeight = o.top) : (this.scrollAnchorPos = -1, this.scrollAnchorHeight = a);
		let s = i.length ? this.mapViewport(this.viewport, e.changes) : this.viewport;
		(t && (t.range.head < s.from || t.range.head > s.to) || !this.viewportIsAppropriate(s)) && (s = this.getViewport(0, t));
		let c = s.from != this.viewport.from || s.to != this.viewport.to;
		this.viewport = s, e.flags |= this.updateForViewport(), (c || !e.changes.empty || e.flags & 2) && this.updateViewportLines(), (this.lineGaps.length || this.viewport.to - this.viewport.from > 4e3) && this.updateLineGaps(this.ensureLineGaps(this.mapLineGaps(this.lineGaps, e.changes))), e.flags |= this.computeVisibleRanges(e.changes), t && (this.scrollTarget = t), !this.mustEnforceCursorAssoc && (e.selectionSet || e.focusChanged) && e.view.lineWrapping && e.state.selection.main.empty && e.state.selection.main.assoc && !e.state.facet(Jr) && (this.mustEnforceCursorAssoc = !0);
	}
	measure() {
		let { view: e } = this, t = e.contentDOM, n = window.getComputedStyle(t), r = this.heightOracle, i = n.whiteSpace;
		this.defaultTextDirection = n.direction == "rtl" ? V.RTL : V.LTR;
		let a = this.heightOracle.mustRefreshForWrapping(i) || this.mustMeasureContent === "refresh", o = t.getBoundingClientRect(), s = a || this.mustMeasureContent || this.contentDOMHeight != o.height;
		this.contentDOMHeight = o.height, this.mustMeasureContent = !1;
		let c = 0, l = 0;
		if (o.width && o.height) {
			let { scaleX: e, scaleY: n } = er(t, o);
			(e > .005 && Math.abs(this.scaleX - e) > .005 || n > .005 && Math.abs(this.scaleY - n) > .005) && (this.scaleX = e, this.scaleY = n, c |= 16, a = s = !0);
		}
		let u = (parseInt(n.paddingTop) || 0) * this.scaleY, d = (parseInt(n.paddingBottom) || 0) * this.scaleY;
		(this.paddingTop != u || this.paddingBottom != d) && (this.paddingTop = u, this.paddingBottom = d, c |= 18), this.editorWidth != e.scrollDOM.clientWidth && (r.lineWrapping && (s = !0), this.editorWidth = e.scrollDOM.clientWidth, c |= 16);
		let f = nr(this.view.contentDOM, !1).y;
		f != this.scrollParent && (this.scrollParent = f, this.scrollAnchorHeight = -1, this.scrollOffset = 0);
		let p = this.getScrollOffset();
		this.scrollOffset != p && (this.scrollAnchorHeight = -1, this.scrollOffset = p), this.scrolledToBottom = pr(this.scrollParent || e.win);
		let m = (this.printing ? Po : Mo)(t, this.paddingTop), h = m.top - this.pixelViewport.top, g = m.bottom - this.pixelViewport.bottom;
		this.pixelViewport = m;
		let _ = this.pixelViewport.bottom > this.pixelViewport.top && this.pixelViewport.right > this.pixelViewport.left;
		if (_ != this.inView && (this.inView = _, _ && (s = !0)), !this.inView && !this.scrollTarget && !No(e.dom)) return 0;
		let v = o.width;
		if ((this.contentDOMWidth != v || this.editorHeight != e.scrollDOM.clientHeight) && (this.contentDOMWidth = o.width, this.editorHeight = e.scrollDOM.clientHeight, c |= 16), s) {
			let t = e.docView.measureVisibleLineHeights(this.viewport);
			if (r.mustRefreshForHeights(t) && (a = !0), a || r.lineWrapping && Math.abs(v - this.contentDOMWidth) > r.charWidth) {
				let { lineHeight: n, charWidth: o, textHeight: s } = e.docView.measureTextSize();
				a = n > 0 && r.refresh(i, n, o, s, Math.max(5, v / o), t), a && (e.docView.minWidth = 0, c |= 16);
			}
			h > 0 && g > 0 ? l = Math.max(h, g) : h < 0 && g < 0 && (l = Math.min(h, g)), ho();
			for (let n of this.viewports) {
				let i = n.from == this.viewport.from ? t : e.docView.measureVisibleLineHeights(n);
				this.heightMap = (a ? bo.empty().applyChanges(this.stateDeco, C.empty, this.heightOracle, [new mi(0, 0, 0, e.state.doc.length)]) : this.heightMap).updateHeight(r, 0, a, new _o(n.from, i));
			}
			mo && (c |= 2);
		}
		let y = !this.viewportIsAppropriate(this.viewport, l) || this.scrollTarget && (this.scrollTarget.range.head < this.viewport.from || this.scrollTarget.range.head > this.viewport.to);
		return y && (c & 2 && (c |= this.updateScaler()), this.viewport = this.getViewport(l, this.scrollTarget), c |= this.updateForViewport()), (c & 2 || y) && this.updateViewportLines(), (this.lineGaps.length || this.viewport.to - this.viewport.from > 4e3) && this.updateLineGaps(this.ensureLineGaps(a ? [] : this.lineGaps, e)), c |= this.computeVisibleRanges(), this.mustEnforceCursorAssoc && (this.mustEnforceCursorAssoc = !1, e.docView.enforceCursorAssoc()), c;
	}
	get visibleTop() {
		return this.scaler.fromDOM(this.pixelViewport.top);
	}
	get visibleBottom() {
		return this.scaler.fromDOM(this.pixelViewport.bottom);
	}
	getViewport(e, t) {
		let n = .5 - Math.max(-.5, Math.min(.5, e / 1e3 / 2)), r = this.heightMap, i = this.heightOracle, { visibleTop: a, visibleBottom: o } = this, s = new Ro(r.lineAt(a - n * 1e3, q.ByHeight, i, 0, 0).from, r.lineAt(o + (1 - n) * 1e3, q.ByHeight, i, 0, 0).to);
		if (t) {
			let { head: e } = t.range;
			if (e < s.from || e > s.to) {
				let n = Math.min(this.editorHeight, this.pixelViewport.bottom - this.pixelViewport.top), a = r.lineAt(e, q.ByPos, i, 0, 0), o;
				o = t.y == "center" ? (a.top + a.bottom) / 2 - n / 2 : t.y == "start" || t.y == "nearest" && e < s.from ? a.top : a.bottom - n, s = new Ro(r.lineAt(o - 500, q.ByHeight, i, 0, 0).from, r.lineAt(o + n + 500, q.ByHeight, i, 0, 0).to);
			}
		}
		return s;
	}
	mapViewport(e, t) {
		let n = t.mapPos(e.from, -1), r = t.mapPos(e.to, 1);
		return new Ro(this.heightMap.lineAt(n, q.ByPos, this.heightOracle, 0, 0).from, this.heightMap.lineAt(r, q.ByPos, this.heightOracle, 0, 0).to);
	}
	viewportIsAppropriate({ from: e, to: t }, n = 0) {
		if (!this.inView) return !0;
		let { top: r } = this.heightMap.lineAt(e, q.ByPos, this.heightOracle, 0, 0), { bottom: i } = this.heightMap.lineAt(t, q.ByPos, this.heightOracle, 0, 0), { visibleTop: a, visibleBottom: o } = this;
		return (e == 0 || r <= a - Math.max(10, Math.min(-n, 250))) && (t == this.state.doc.length || i >= o + Math.max(10, Math.min(n, 250))) && r > a - 2e3 && i < o + 2e3;
	}
	mapLineGaps(e, t) {
		if (!e.length || t.empty) return e;
		let n = [];
		for (let r of e) t.touchesRange(r.from, r.to) || n.push(new Fo(t.mapPos(r.from), t.mapPos(r.to), r.size, r.displaySize));
		return n;
	}
	ensureLineGaps(e, t) {
		let n = this.heightOracle.lineWrapping, r = n ? 1e4 : 2e3, i = r >> 1, a = r << 1;
		if (this.defaultTextDirection != V.LTR && !n) return [];
		let o = [], s = (r, a, c, l) => {
			if (a - r < i) return;
			let u = this.state.selection.main, d = [u.from];
			u.empty || d.push(u.to);
			for (let e of d) if (e > r && e < a) {
				s(r, e - 10, c, l), s(e + 10, a, c, l);
				return;
			}
			let f = Ho(e, (e) => e.from >= c.from && e.to <= c.to && Math.abs(e.from - r) < i && Math.abs(e.to - a) < i && !d.some((t) => e.from < t && e.to > t));
			if (!f) {
				if (a < c.to && t && n && t.visibleRanges.some((e) => e.from <= a && e.to >= a)) {
					let e = t.moveToLineBoundary(D.cursor(a), !1, !0).head;
					e > r && (a = e);
				}
				let e = this.gapSize(c, r, a, l);
				f = new Fo(r, a, e, n || e < 2e6 ? e : 2e6);
			}
			o.push(f);
		}, c = (t) => {
			if (t.length < a || t.type != z.Text) return;
			let i = zo(t.from, t.to, this.stateDeco);
			if (i.total < a) return;
			let o = this.scrollTarget ? this.scrollTarget.range.head : null, c, l;
			if (n) {
				let e = r / this.heightOracle.lineLength * this.heightOracle.lineHeight, n, a;
				if (o != null) {
					let r = Vo(i, o), s = ((this.visibleBottom - this.visibleTop) / 2 + e) / t.height;
					n = r - s, a = r + s;
				} else n = (this.visibleTop - t.top - e) / t.height, a = (this.visibleBottom - t.top + e) / t.height;
				c = Bo(i, n), l = Bo(i, a);
			} else {
				let n = i.total * this.heightOracle.charWidth, a = r * this.heightOracle.charWidth, s = 0;
				if (n > 2e6) for (let n of e) n.from >= t.from && n.from < t.to && n.size != n.displaySize && n.from * this.heightOracle.charWidth + s < this.pixelViewport.left && (s = n.size - n.displaySize);
				let u = this.pixelViewport.left + s, d = this.pixelViewport.right + s, f, p;
				if (o != null) {
					let e = Vo(i, o), t = ((d - u) / 2 + a) / n;
					f = e - t, p = e + t;
				} else f = (u - a) / n, p = (d + a) / n;
				c = Bo(i, f), l = Bo(i, p);
			}
			c > t.from && s(t.from, c, t, i), l < t.to && s(l, t.to, t, i);
		};
		for (let e of this.viewportLines) Array.isArray(e.type) ? e.type.forEach(c) : c(e);
		return o;
	}
	gapSize(e, t, n, r) {
		let i = Vo(r, n) - Vo(r, t);
		return this.heightOracle.lineWrapping ? e.height * i : r.total * this.heightOracle.charWidth * i;
	}
	updateLineGaps(e) {
		Fo.same(e, this.lineGaps) || (this.lineGaps = e, this.lineGapDeco = B.set(e.map((e) => e.draw(this, this.heightOracle.lineWrapping))));
	}
	computeVisibleRanges(e) {
		let t = this.stateDeco;
		this.lineGaps.length && (t = t.concat(this.lineGapDeco));
		let n = [];
		P.spans(t, this.viewport.from, this.viewport.to, {
			span(e, t) {
				n.push({
					from: e,
					to: t
				});
			},
			point() {}
		}, 20);
		let r = 0;
		if (n.length != this.visibleRanges.length) r = 12;
		else for (let t = 0; t < n.length && !(r & 8); t++) {
			let i = this.visibleRanges[t], a = n[t];
			(i.from != a.from || i.to != a.to) && (r |= 4, e && e.mapPos(i.from, -1) == a.from && e.mapPos(i.to, 1) == a.to || (r |= 8));
		}
		return this.visibleRanges = n, r;
	}
	lineBlockAt(e) {
		return e >= this.viewport.from && e <= this.viewport.to && this.viewportLines.find((t) => t.from <= e && t.to >= e) || Ko(this.heightMap.lineAt(e, q.ByPos, this.heightOracle, 0, 0), this.scaler);
	}
	lineBlockAtHeight(e) {
		return e >= this.viewportLines[0].top && e <= this.viewportLines[this.viewportLines.length - 1].bottom && this.viewportLines.find((t) => t.top <= e && t.bottom >= e) || Ko(this.heightMap.lineAt(this.scaler.fromDOM(e), q.ByHeight, this.heightOracle, 0, 0), this.scaler);
	}
	getScrollOffset() {
		return (this.scrollParent == this.view.scrollDOM ? this.scrollParent.scrollTop : (this.scrollParent ? this.scrollParent.getBoundingClientRect().top : 0) - this.view.contentDOM.getBoundingClientRect().top) * this.scaleY;
	}
	scrollAnchorAt(e) {
		let t = this.lineBlockAtHeight(e + 8);
		return t.from >= this.viewport.from || this.viewportLines[0].top - e > 200 ? t : this.viewportLines[0];
	}
	elementAtHeight(e) {
		return Ko(this.heightMap.blockAt(this.scaler.fromDOM(e), this.heightOracle, 0, 0), this.scaler);
	}
	get docHeight() {
		return this.scaler.toDOM(this.heightMap.height);
	}
	get contentHeight() {
		return this.docHeight + this.paddingTop + this.paddingBottom;
	}
}, Ro = class {
	constructor(e, t) {
		this.from = e, this.to = t;
	}
};
function zo(e, t, n) {
	let r = [], i = e, a = 0;
	return P.spans(n, e, t, {
		span() {},
		point(e, t) {
			e > i && (r.push({
				from: i,
				to: e
			}), a += e - i), i = t;
		}
	}, 20), i < t && (r.push({
		from: i,
		to: t
	}), a += t - i), {
		total: a,
		ranges: r
	};
}
function Bo({ total: e, ranges: t }, n) {
	if (n <= 0) return t[0].from;
	if (n >= 1) return t[t.length - 1].to;
	let r = Math.floor(e * n);
	for (let e = 0;; e++) {
		let { from: n, to: i } = t[e], a = i - n;
		if (r <= a) return n + r;
		r -= a;
	}
}
function Vo(e, t) {
	let n = 0;
	for (let { from: r, to: i } of e.ranges) {
		if (t <= i) {
			n += t - r;
			break;
		}
		n += i - r;
	}
	return n / e.total;
}
function Ho(e, t) {
	for (let n of e) if (t(n)) return n;
}
var Uo = {
	toDOM(e) {
		return e;
	},
	fromDOM(e) {
		return e;
	},
	scale: 1,
	eq(e) {
		return e == this;
	}
};
function Wo(e) {
	let t = e.facet(ai).filter((e) => typeof e != "function"), n = e.facet(si).filter((e) => typeof e != "function");
	return n.length && t.push(P.join(n)), t;
}
var Go = class e {
	constructor(e, t, n) {
		let r = 0, i = 0, a = 0;
		this.viewports = n.map(({ from: n, to: i }) => {
			let a = t.lineAt(n, q.ByPos, e, 0, 0).top, o = t.lineAt(i, q.ByPos, e, 0, 0).bottom;
			return r += o - a, {
				from: n,
				to: i,
				top: a,
				bottom: o,
				domTop: 0,
				domBottom: 0
			};
		}), this.scale = (7e6 - r) / (t.height - r);
		for (let e of this.viewports) e.domTop = a + (e.top - i) * this.scale, a = e.domBottom = e.domTop + (e.bottom - e.top), i = e.bottom;
	}
	toDOM(e) {
		for (let t = 0, n = 0, r = 0;; t++) {
			let i = t < this.viewports.length ? this.viewports[t] : null;
			if (!i || e < i.top) return r + (e - n) * this.scale;
			if (e <= i.bottom) return i.domTop + (e - i.top);
			n = i.bottom, r = i.domBottom;
		}
	}
	fromDOM(e) {
		for (let t = 0, n = 0, r = 0;; t++) {
			let i = t < this.viewports.length ? this.viewports[t] : null;
			if (!i || e < i.domTop) return n + (e - r) / this.scale;
			if (e <= i.domBottom) return i.top + (e - i.domTop);
			n = i.bottom, r = i.domBottom;
		}
	}
	eq(t) {
		return t instanceof e && this.scale == t.scale && this.viewports.length == t.viewports.length && this.viewports.every((e, n) => e.from == t.viewports[n].from && e.to == t.viewports[n].to);
	}
};
function Ko(e, t) {
	if (t.scale == 1) return e;
	let n = t.toDOM(e.top), r = t.toDOM(e.bottom);
	return new vo(e.from, e.length, n, r - n, Array.isArray(e._content) ? e._content.map((e) => Ko(e, t)) : e._content);
}
var qo = /*@__PURE__*/ O.define({ combine: (e) => e.join(" ") }), Jo = /*@__PURE__*/ O.define({ combine: (e) => e.indexOf(!0) > -1 }), Yo = /*@__PURE__*/ nn.newName(), Xo = /*@__PURE__*/ nn.newName(), Zo = /*@__PURE__*/ nn.newName(), Qo = {
	"&light": "." + Xo,
	"&dark": "." + Zo
};
function $o(e, t, n) {
	return new nn(t, { finish(t) {
		return /&/.test(t) ? t.replace(/&\w*/, (t) => {
			if (t == "&") return e;
			if (!n || !n[t]) throw RangeError(`Unsupported selector: ${t}`);
			return n[t];
		}) : e + " " + t;
	} });
}
var es = /*@__PURE__*/ $o("." + Yo, {
	"&": {
		position: "relative !important",
		boxSizing: "border-box",
		"&.cm-focused": { outline: "1px dotted #212121" },
		display: "flex !important",
		flexDirection: "column"
	},
	".cm-scroller": {
		display: "flex !important",
		alignItems: "flex-start !important",
		fontFamily: "monospace",
		lineHeight: 1.4,
		height: "100%",
		overflowX: "auto",
		position: "relative",
		zIndex: 0,
		overflowAnchor: "none"
	},
	".cm-content": {
		margin: 0,
		flexGrow: 2,
		flexShrink: 0,
		display: "block",
		whiteSpace: "pre",
		wordWrap: "normal",
		boxSizing: "border-box",
		minHeight: "100%",
		padding: "4px 0",
		outline: "none",
		"&[contenteditable=true]": { WebkitUserModify: "read-write-plaintext-only" }
	},
	".cm-lineWrapping": {
		whiteSpace_fallback: "pre-wrap",
		whiteSpace: "break-spaces",
		wordBreak: "break-word",
		overflowWrap: "anywhere",
		flexShrink: 1
	},
	"&light .cm-content": { caretColor: "black" },
	"&dark .cm-content": { caretColor: "white" },
	".cm-line": {
		display: "block",
		padding: "0 2px 0 6px"
	},
	".cm-layer": {
		userSelect: "none",
		position: "absolute",
		left: 0,
		top: 0,
		contain: "size style",
		"& > *": { position: "absolute" }
	},
	"&light .cm-selectionBackground": { background: "#d9d9d9" },
	"&dark .cm-selectionBackground": { background: "#222" },
	"&light.cm-focused > .cm-scroller > .cm-selectionLayer .cm-selectionBackground": { background: "#d7d4f0" },
	"&dark.cm-focused > .cm-scroller > .cm-selectionLayer .cm-selectionBackground": { background: "#233" },
	".cm-cursorLayer": { pointerEvents: "none" },
	"&.cm-focused > .cm-scroller > .cm-cursorLayer": { animation: "steps(1) cm-blink 1.2s infinite" },
	"@keyframes cm-blink": {
		"0%": {},
		"50%": { opacity: 0 },
		"100%": {}
	},
	"@keyframes cm-blink2": {
		"0%": {},
		"50%": { opacity: 0 },
		"100%": {}
	},
	".cm-cursor, .cm-dropCursor": {
		borderLeft: "1.2px solid black",
		marginLeft: "-0.6px",
		pointerEvents: "none"
	},
	".cm-cursor": { display: "none" },
	"&dark .cm-cursor": { borderLeftColor: "#ddd" },
	".cm-selectionHandle": {
		backgroundColor: "currentColor",
		width: "1.5px"
	},
	".cm-selectionHandle-start::before, .cm-selectionHandle-end::before": {
		content: "\"\"",
		backgroundColor: "inherit",
		borderRadius: "50%",
		width: "8px",
		height: "8px",
		position: "absolute",
		left: "-3.25px"
	},
	".cm-selectionHandle-start::before": { top: "-8px" },
	".cm-selectionHandle-end::before": { bottom: "-8px" },
	".cm-dropCursor": { position: "absolute" },
	"&.cm-focused > .cm-scroller > .cm-cursorLayer .cm-cursor": { display: "block" },
	".cm-iso": { unicodeBidi: "isolate" },
	".cm-announced": {
		position: "fixed",
		top: "-10000px"
	},
	"@media print": { ".cm-announced": { display: "none" } },
	"&light .cm-activeLine": { backgroundColor: "#cceeff44" },
	"&dark .cm-activeLine": { backgroundColor: "#99eeff33" },
	"&light .cm-specialChar": { color: "red" },
	"&dark .cm-specialChar": { color: "#f78" },
	".cm-gutters": {
		flexShrink: 0,
		display: "flex",
		height: "100%",
		boxSizing: "border-box",
		zIndex: 200
	},
	".cm-gutters-before": { insetInlineStart: 0 },
	".cm-gutters-after": { insetInlineEnd: 0 },
	"&light .cm-gutters": {
		backgroundColor: "#f5f5f5",
		color: "#6c6c6c",
		border: "0px solid #ddd",
		"&.cm-gutters-before": { borderRightWidth: "1px" },
		"&.cm-gutters-after": { borderLeftWidth: "1px" }
	},
	"&dark .cm-gutters": {
		backgroundColor: "#333338",
		color: "#ccc"
	},
	".cm-gutter": {
		display: "flex !important",
		flexDirection: "column",
		flexShrink: 0,
		boxSizing: "border-box",
		minHeight: "100%",
		overflow: "hidden"
	},
	".cm-gutterElement": { boxSizing: "border-box" },
	".cm-lineNumbers .cm-gutterElement": {
		padding: "0 3px 0 5px",
		minWidth: "20px",
		textAlign: "right",
		whiteSpace: "nowrap"
	},
	"&light .cm-activeLineGutter": { backgroundColor: "#e2f2ff" },
	"&dark .cm-activeLineGutter": { backgroundColor: "#222227" },
	".cm-panels": {
		boxSizing: "border-box",
		position: "sticky",
		left: 0,
		right: 0,
		zIndex: 300
	},
	"&light .cm-panels": {
		backgroundColor: "#f5f5f5",
		color: "black"
	},
	".cm-panels-top": { top: "0" },
	".cm-panels-bottom": { bottom: "0" },
	"&light .cm-panels-top": { borderBottom: "1px solid #ddd" },
	"&light .cm-panels-bottom": { borderTop: "1px solid #ddd" },
	"&dark .cm-panels": {
		backgroundColor: "#333338",
		color: "white"
	},
	".cm-dialog": {
		padding: "2px 19px 4px 6px",
		position: "relative",
		"& label": { fontSize: "80%" }
	},
	".cm-dialog-close": {
		position: "absolute",
		top: "3px",
		right: "4px",
		backgroundColor: "inherit",
		border: "none",
		font: "inherit",
		fontSize: "14px",
		padding: "0"
	},
	".cm-tab": {
		display: "inline-block",
		overflow: "hidden",
		verticalAlign: "bottom"
	},
	".cm-widgetBuffer": {
		verticalAlign: "text-top",
		height: "1em",
		width: 0,
		display: "inline"
	},
	".cm-placeholder": {
		color: "#888",
		display: "inline-block",
		verticalAlign: "top",
		userSelect: "none"
	},
	".cm-highlightSpace": {
		backgroundImage: "radial-gradient(circle at 50% 55%, #aaa 20%, transparent 5%)",
		backgroundPosition: "center"
	},
	".cm-highlightTab": {
		backgroundImage: "url('data:image/svg+xml,<svg xmlns=\"http://www.w3.org/2000/svg\" width=\"200\" height=\"20\"><path stroke=\"%23888\" stroke-width=\"1\" fill=\"none\" d=\"M1 10H196L190 5M190 15L196 10M197 4L197 16\"/></svg>')",
		backgroundSize: "auto 100%",
		backgroundPosition: "right 90%",
		backgroundRepeat: "no-repeat"
	},
	".cm-trailingSpace": { backgroundColor: "#ff332255" },
	".cm-button": {
		verticalAlign: "middle",
		color: "inherit",
		fontSize: "70%",
		padding: ".2em 1em",
		borderRadius: "1px"
	},
	"&light .cm-button": {
		backgroundImage: "linear-gradient(#eff1f5, #d9d9df)",
		border: "1px solid #888",
		"&:active": { backgroundImage: "linear-gradient(#b4b4b4, #d0d3d6)" }
	},
	"&dark .cm-button": {
		backgroundImage: "linear-gradient(#393939, #111)",
		border: "1px solid #888",
		"&:active": { backgroundImage: "linear-gradient(#111, #333)" }
	},
	".cm-textfield": {
		verticalAlign: "middle",
		color: "inherit",
		fontSize: "70%",
		border: "1px solid silver",
		padding: ".2em .5em"
	},
	"&light .cm-textfield": { backgroundColor: "white" },
	"&dark .cm-textfield": {
		border: "1px solid #555",
		backgroundColor: "inherit"
	}
}, Qo), ts = {
	childList: !0,
	characterData: !0,
	subtree: !0,
	attributes: !0,
	characterDataOldValue: !0
}, ns = R.ie && R.ie_version <= 11, rs = class {
	constructor(e) {
		this.view = e, this.active = !1, this.editContext = null, this.selectionRange = new rr(), this.selectionChanged = !1, this.delayedFlush = -1, this.resizeTimeout = -1, this.queue = [], this.delayedAndroidKey = null, this.flushingAndroidKey = -1, this.lastChange = 0, this.scrollTargets = [], this.intersection = null, this.resizeScroll = null, this.intersecting = !1, this.gapIntersection = null, this.gaps = [], this.printQuery = null, this.parentCheck = -1, this.dom = e.contentDOM, this.observer = new MutationObserver((t) => {
			for (let e of t) this.queue.push(e);
			(R.ie && R.ie_version <= 11 || R.ios && e.composing) && t.some((e) => e.type == "childList" && e.removedNodes.length || e.type == "characterData" && e.oldValue.length > e.target.nodeValue.length) ? this.flushSoon() : this.flush();
		}), window.EditContext && R.android && e.constructor.EDIT_CONTEXT !== !1 && !(R.chrome && R.chrome_version < 126) && (this.editContext = new ss(e), e.state.facet($r) && (e.contentDOM.editContext = this.editContext.editContext)), ns && (this.onCharData = (e) => {
			this.queue.push({
				target: e.target,
				type: "characterData",
				oldValue: e.prevValue
			}), this.flushSoon();
		}), this.onSelectionChange = this.onSelectionChange.bind(this), this.onResize = this.onResize.bind(this), this.onPrint = this.onPrint.bind(this), this.onScroll = this.onScroll.bind(this), window.matchMedia && (this.printQuery = window.matchMedia("print")), typeof ResizeObserver == "function" && (this.resizeScroll = new ResizeObserver(() => {
			var e;
			((e = this.view.docView) == null ? void 0 : e.lastUpdate) < Date.now() - 75 && this.onResize();
		}), this.resizeScroll.observe(e.scrollDOM)), this.addWindowListeners(this.win = e.win), this.start(), typeof IntersectionObserver == "function" && (this.intersection = new IntersectionObserver((e) => {
			this.parentCheck < 0 && (this.parentCheck = setTimeout(this.listenForScroll.bind(this), 1e3)), e.length > 0 && e[e.length - 1].intersectionRatio > 0 != this.intersecting && (this.intersecting = !this.intersecting, this.intersecting != this.view.inView && this.onScrollChanged(document.createEvent("Event")));
		}, { threshold: [0, .001] }), this.intersection.observe(this.dom), this.gapIntersection = new IntersectionObserver((e) => {
			e.length > 0 && e[e.length - 1].intersectionRatio > 0 && this.onScrollChanged(document.createEvent("Event"));
		}, {})), this.listenForScroll(), this.readSelectionRange();
	}
	onScrollChanged(e) {
		this.view.inputState.runHandlers("scroll", e), this.intersecting && this.view.measure();
	}
	onScroll(e) {
		this.intersecting && this.flush(!1), this.editContext && this.view.requestMeasure(this.editContext.measureReq), this.onScrollChanged(e);
	}
	onResize() {
		this.resizeTimeout < 0 && (this.resizeTimeout = setTimeout(() => {
			this.resizeTimeout = -1, this.view.requestMeasure();
		}, 50));
	}
	onPrint(e) {
		(e.type == "change" || !e.type) && !e.matches || (this.view.viewState.printing = !0, this.view.measure(), setTimeout(() => {
			this.view.viewState.printing = !1, this.view.requestMeasure();
		}, 500));
	}
	updateGaps(e) {
		if (this.gapIntersection && (e.length != this.gaps.length || this.gaps.some((t, n) => t != e[n]))) {
			this.gapIntersection.disconnect();
			for (let t of e) this.gapIntersection.observe(t);
			this.gaps = e;
		}
	}
	onSelectionChange(e) {
		let t = this.selectionChanged;
		if (!this.readSelectionRange() || this.delayedAndroidKey) return;
		let { view: n } = this, r = this.selectionRange;
		if (n.state.facet($r) ? n.root.activeElement != this.dom : !Gn(this.dom, r)) return;
		let i = r.anchorNode && n.docView.tile.nearest(r.anchorNode);
		if (i && i.isWidget() && i.widget.ignoreEvent(e)) {
			t || (this.selectionChanged = !1);
			return;
		}
		(R.ie && R.ie_version <= 11 || R.android && R.chrome) && !n.state.selection.main.empty && r.focusNode && qn(r.focusNode, r.focusOffset, r.anchorNode, r.anchorOffset) ? this.flushSoon() : this.flush(!1);
	}
	readSelectionRange() {
		let { view: e } = this, t = Un(e.root);
		if (!t) return !1;
		let n = R.safari && e.root.nodeType == 11 && e.root.activeElement == this.dom && os(this.view, t) || t;
		if (!n || this.selectionRange.eq(n)) return !1;
		let r = Gn(this.dom, n);
		return r && !this.selectionChanged && e.inputState.lastFocusTime > Date.now() - 200 && e.inputState.lastTouchTime < Date.now() - 300 && fr(this.dom, n) ? (this.view.inputState.lastFocusTime = 0, e.docView.updateSelection(), !1) : (this.selectionRange.setRange(n), r && (this.selectionChanged = !0), !0);
	}
	setSelectionRange(e, t) {
		this.selectionRange.set(e.node, e.offset, t.node, t.offset), this.selectionChanged = !1;
	}
	clearSelectionRange() {
		this.selectionRange.set(null, 0, null, 0);
	}
	listenForScroll() {
		this.parentCheck = -1;
		let e = 0, t = null;
		for (let n = this.dom; n;) if (n.nodeType == 1) !t && e < this.scrollTargets.length && this.scrollTargets[e] == n ? e++ : t || (t = this.scrollTargets.slice(0, e)), t && t.push(n), n = n.assignedSlot || n.parentNode;
		else if (n.nodeType == 11) n = n.host;
		else break;
		if (e < this.scrollTargets.length && !t && (t = this.scrollTargets.slice(0, e)), t) {
			for (let e of this.scrollTargets) e.removeEventListener("scroll", this.onScroll);
			for (let e of this.scrollTargets = t) e.addEventListener("scroll", this.onScroll);
		}
	}
	ignore(e) {
		if (!this.active) return e();
		try {
			return this.stop(), e();
		} finally {
			this.start(), this.clear();
		}
	}
	start() {
		this.active || (this.observer.observe(this.dom, ts), ns && this.dom.addEventListener("DOMCharacterDataModified", this.onCharData), this.active = !0);
	}
	stop() {
		this.active && (this.active = !1, this.observer.disconnect(), ns && this.dom.removeEventListener("DOMCharacterDataModified", this.onCharData));
	}
	clear() {
		this.processRecords(), this.queue.length = 0, this.selectionChanged = !1;
	}
	delayAndroidKey(e, t) {
		var n;
		if (!this.delayedAndroidKey) {
			let e = () => {
				let e = this.delayedAndroidKey;
				e && (this.clearDelayedAndroidKey(), this.view.inputState.lastKeyCode = e.keyCode, this.view.inputState.lastKeyTime = Date.now(), !this.flush() && e.force && ur(this.dom, e.key, e.keyCode));
			};
			this.flushingAndroidKey = this.view.win.requestAnimationFrame(e);
		}
		(!this.delayedAndroidKey || e == "Enter") && (this.delayedAndroidKey = {
			key: e,
			keyCode: t,
			force: this.lastChange < Date.now() - 50 || !!((n = this.delayedAndroidKey) != null && n.force)
		});
	}
	clearDelayedAndroidKey() {
		this.win.cancelAnimationFrame(this.flushingAndroidKey), this.delayedAndroidKey = null, this.flushingAndroidKey = -1;
	}
	flushSoon() {
		this.delayedFlush < 0 && (this.delayedFlush = this.view.win.requestAnimationFrame(() => {
			this.delayedFlush = -1, this.flush();
		}));
	}
	forceFlush() {
		this.delayedFlush >= 0 && (this.view.win.cancelAnimationFrame(this.delayedFlush), this.delayedFlush = -1), this.flush();
	}
	pendingRecords() {
		for (let e of this.observer.takeRecords()) this.queue.push(e);
		return this.queue;
	}
	processRecords() {
		let e = this.pendingRecords();
		e.length && (this.queue = []);
		let t = -1, n = -1, r = !1;
		for (let i of e) {
			let e = this.readMutation(i);
			e && (e.typeOver && (r = !0), t == -1 ? {from: t, to: n} = e : (t = Math.min(e.from, t), n = Math.max(e.to, n)));
		}
		return {
			from: t,
			to: n,
			typeOver: r
		};
	}
	readChange() {
		let { from: e, to: t, typeOver: n } = this.processRecords(), r = this.selectionChanged && Gn(this.dom, this.selectionRange);
		if (e < 0 && !r) return null;
		e > -1 && (this.lastChange = Date.now()), this.view.inputState.lastFocusTime = 0, this.selectionChanged = !1;
		let i = new ba(this.view, e, t, n);
		return this.view.docView.domChanged = { newSel: i.newSel ? i.newSel.main : null }, i;
	}
	flush(e = !0) {
		if (this.delayedFlush >= 0 || this.delayedAndroidKey) return !1;
		e && this.readSelectionRange();
		let t = this.readChange();
		if (!t) return this.view.requestMeasure(), !1;
		let n = this.view.state, r = Sa(this.view, t);
		return this.view.state == n && (t.domChanged || t.newSel && !Oa(this.view.state.selection, t.newSel.main)) && this.view.update([]), r;
	}
	readMutation(e) {
		let t = this.view.docView.tile.nearest(e.target);
		if (!t || t.isWidget()) return null;
		if (t.markDirty(e.type == "attributes"), e.type == "childList") {
			let n = is(t, e.previousSibling || e.target.previousSibling, -1), r = is(t, e.nextSibling || e.target.nextSibling, 1);
			return {
				from: n ? t.posAfter(n) : t.posAtStart,
				to: r ? t.posBefore(r) : t.posAtEnd,
				typeOver: !1
			};
		}
		return e.type == "characterData" ? {
			from: t.posAtStart,
			to: t.posAtEnd,
			typeOver: e.target.nodeValue == e.oldValue
		} : null;
	}
	setWindow(e) {
		e != this.win && (this.removeWindowListeners(this.win), this.win = e, this.addWindowListeners(this.win));
	}
	addWindowListeners(e) {
		e.addEventListener("resize", this.onResize), this.printQuery ? this.printQuery.addEventListener ? this.printQuery.addEventListener("change", this.onPrint) : this.printQuery.addListener(this.onPrint) : e.addEventListener("beforeprint", this.onPrint), e.addEventListener("scroll", this.onScroll), e.document.addEventListener("selectionchange", this.onSelectionChange);
	}
	removeWindowListeners(e) {
		e.removeEventListener("scroll", this.onScroll), e.removeEventListener("resize", this.onResize), this.printQuery ? this.printQuery.removeEventListener ? this.printQuery.removeEventListener("change", this.onPrint) : this.printQuery.removeListener(this.onPrint) : e.removeEventListener("beforeprint", this.onPrint), e.document.removeEventListener("selectionchange", this.onSelectionChange);
	}
	update(e) {
		this.editContext && (this.editContext.update(e), e.startState.facet($r) != e.state.facet($r) && (e.view.contentDOM.editContext = e.state.facet($r) ? this.editContext.editContext : null));
	}
	destroy() {
		var e, t, n;
		this.stop(), (e = this.intersection) == null || e.disconnect(), (t = this.gapIntersection) == null || t.disconnect(), (n = this.resizeScroll) == null || n.disconnect();
		for (let e of this.scrollTargets) e.removeEventListener("scroll", this.onScroll);
		this.removeWindowListeners(this.win), clearTimeout(this.parentCheck), clearTimeout(this.resizeTimeout), this.win.cancelAnimationFrame(this.delayedFlush), this.win.cancelAnimationFrame(this.flushingAndroidKey), this.editContext && (this.view.contentDOM.editContext = null, this.editContext.destroy());
	}
};
function is(e, t, n) {
	for (; t;) {
		let r = G.get(t);
		if (r && r.parent == e) return r;
		let i = t.parentNode;
		t = i == e.dom ? n > 0 ? t.nextSibling : t.previousSibling : i;
	}
	return null;
}
function as(e, t) {
	let n = t.startContainer, r = t.startOffset, i = t.endContainer, a = t.endOffset, o = e.docView.domAtPos(e.state.selection.main.anchor, 1);
	return qn(o.node, o.offset, i, a) && ([n, r, i, a] = [
		i,
		a,
		n,
		r
	]), {
		anchorNode: n,
		anchorOffset: r,
		focusNode: i,
		focusOffset: a
	};
}
function os(e, t) {
	if (t.getComposedRanges) {
		let n = t.getComposedRanges(e.root)[0];
		if (n) return as(e, n);
	}
	let n = null;
	function r(e) {
		e.preventDefault(), e.stopImmediatePropagation(), n = e.getTargetRanges()[0];
	}
	return e.contentDOM.addEventListener("beforeinput", r, !0), e.dom.ownerDocument.execCommand("indent"), e.contentDOM.removeEventListener("beforeinput", r, !0), n ? as(e, n) : null;
}
var ss = class {
	constructor(e) {
		this.from = 0, this.to = 0, this.pendingContextChange = null, this.handlers = Object.create(null), this.composing = null, this.resetRange(e.state);
		let t = this.editContext = new window.EditContext({
			text: e.state.doc.sliceString(this.from, this.to),
			selectionStart: this.toContextPos(Math.max(this.from, Math.min(this.to, e.state.selection.main.anchor))),
			selectionEnd: this.toContextPos(e.state.selection.main.head)
		});
		this.handlers.textupdate = (n) => {
			let r = e.state.selection.main, { anchor: i, head: a } = r, o = this.toEditorPos(n.updateRangeStart), s = this.toEditorPos(n.updateRangeEnd);
			e.inputState.composing >= 0 && !this.composing && (this.composing = {
				contextBase: n.updateRangeStart,
				editorBase: o,
				drifted: !1
			});
			let c = s - o > n.text.length;
			o == this.from && i < this.from ? o = i : s == this.to && i > this.to && (s = i);
			let l = Ta(e.state.sliceDoc(o, s), n.text, (c ? r.from : r.to) - o, c ? "end" : null);
			if (!l) {
				let t = D.single(this.toEditorPos(n.selectionStart), this.toEditorPos(n.selectionEnd));
				Oa(t, r) || e.dispatch({
					selection: t,
					userEvent: "select"
				});
				return;
			}
			let u = {
				from: l.from + o,
				to: l.toA + o,
				insert: C.of(n.text.slice(l.from, l.toB).split("\n"))
			};
			if ((R.mac || R.android) && u.from == a - 1 && /^\. ?$/.test(n.text) && e.contentDOM.getAttribute("autocorrect") == "off" && (u = {
				from: o,
				to: s,
				insert: C.of([n.text.replace(".", " ")])
			}), this.pendingContextChange = u, !e.state.readOnly) {
				let t = this.to - this.from + (u.to - u.from + u.insert.length);
				Ca(e, u, D.single(this.toEditorPos(n.selectionStart, t), this.toEditorPos(n.selectionEnd, t)));
			}
			this.pendingContextChange && (this.revertPending(e.state), this.setSelection(e.state)), u.from < u.to && !u.insert.length && e.inputState.composing >= 0 && !/[\\p{Alphabetic}\\p{Number}_]/.test(t.text.slice(Math.max(0, n.updateRangeStart - 1), Math.min(t.text.length, n.updateRangeStart + 1))) && this.handlers.compositionend(n);
		}, this.handlers.characterboundsupdate = (n) => {
			let r = [], i = null;
			for (let t = this.toEditorPos(n.rangeStart), a = this.toEditorPos(n.rangeEnd); t < a; t++) {
				let n = e.coordsForChar(t);
				i = n && new DOMRect(n.left, n.top, n.right - n.left, n.bottom - n.top) || i || new DOMRect(), r.push(i);
			}
			t.updateCharacterBounds(n.rangeStart, r);
		}, this.handlers.textformatupdate = (t) => {
			let n = [];
			for (let e of t.getTextFormats()) {
				let t = e.underlineStyle, r = e.underlineThickness;
				if (!/none/i.test(t) && !/none/i.test(r)) {
					let i = this.toEditorPos(e.rangeStart), a = this.toEditorPos(e.rangeEnd);
					if (i < a) {
						let e = `text-decoration: underline ${/^[a-z]/.test(t) ? t + " " : t == "Dashed" ? "dashed " : t == "Squiggle" ? "wavy " : ""}${/thin/i.test(r) ? 1 : 2}px`;
						n.push(B.mark({ attributes: { style: e } }).range(i, a));
					}
				}
			}
			e.dispatch({ effects: Qr.of(B.set(n)) });
		}, this.handlers.compositionstart = () => {
			e.inputState.composing < 0 && (e.inputState.composing = 0, e.inputState.compositionFirstChange = !0);
		}, this.handlers.compositionend = () => {
			if (e.inputState.composing = -1, e.inputState.compositionFirstChange = null, this.composing) {
				let { drifted: t } = this.composing;
				this.composing = null, t && this.reset(e.state);
			}
		};
		for (let e in this.handlers) t.addEventListener(e, this.handlers[e]);
		this.measureReq = { read: (e) => {
			let t = Un(e.root);
			t && t.rangeCount && this.editContext.updateSelectionBounds(t.getRangeAt(0).getBoundingClientRect());
		} };
	}
	applyEdits(e) {
		let t = 0, n = !1, r = this.pendingContextChange;
		return e.changes.iterChanges((i, a, o, s, c) => {
			if (n) return;
			let l = c.length - (a - i);
			if (r && a >= r.to) {
				if (r.from == i && r.to == a && r.insert.eq(c)) {
					r = this.pendingContextChange = null, t += l, this.to += l;
					return;
				}
				r = null, this.revertPending(e.state);
			}
			if (i += t, a += t, a <= this.from) this.from += l, this.to += l;
			else if (i < this.to) {
				if (i < this.from || a > this.to || this.to - this.from + c.length > 3e4) {
					n = !0;
					return;
				}
				this.editContext.updateText(this.toContextPos(i), this.toContextPos(a), c.toString()), this.to += l;
			}
			t += l;
		}), r && !n && this.revertPending(e.state), !n;
	}
	update(e) {
		let t = this.pendingContextChange, n = e.startState.selection.main;
		this.composing && (this.composing.drifted || !e.changes.touchesRange(n.from, n.to) && e.transactions.some((e) => !e.isUserEvent("input.type") && e.changes.touchesRange(this.from, this.to))) ? (this.composing.drifted = !0, this.composing.editorBase = e.changes.mapPos(this.composing.editorBase)) : !this.applyEdits(e) || !this.rangeIsValid(e.state) ? (this.pendingContextChange = null, this.reset(e.state)) : (e.docChanged || e.selectionSet || t) && this.setSelection(e.state), (e.geometryChanged || e.docChanged || e.selectionSet) && e.view.requestMeasure(this.measureReq);
	}
	resetRange(e) {
		let { head: t } = e.selection.main;
		this.from = Math.max(0, t - 1e4), this.to = Math.min(e.doc.length, t + 1e4);
	}
	reset(e) {
		this.resetRange(e), this.editContext.updateText(0, this.editContext.text.length, e.doc.sliceString(this.from, this.to)), this.setSelection(e);
	}
	revertPending(e) {
		let t = this.pendingContextChange;
		this.pendingContextChange = null, this.editContext.updateText(this.toContextPos(t.from), this.toContextPos(t.from + t.insert.length), e.doc.sliceString(t.from, t.to));
	}
	setSelection(e) {
		let { main: t } = e.selection, n = this.toContextPos(Math.max(this.from, Math.min(this.to, t.anchor))), r = this.toContextPos(t.head);
		(this.editContext.selectionStart != n || this.editContext.selectionEnd != r) && this.editContext.updateSelection(n, r);
	}
	rangeIsValid(e) {
		let { head: t } = e.selection.main;
		return !(this.from > 0 && t - this.from < 500 || this.to < e.doc.length && this.to - t < 500 || this.to - this.from > 3e4);
	}
	toEditorPos(e, t = this.to - this.from) {
		e = Math.min(e, t);
		let n = this.composing;
		return n && n.drifted ? n.editorBase + (e - n.contextBase) : e + this.from;
	}
	toContextPos(e) {
		let t = this.composing;
		return t && t.drifted ? t.contextBase + (e - t.editorBase) : e - this.from;
	}
	destroy() {
		for (let e in this.handlers) this.editContext.removeEventListener(e, this.handlers[e]);
	}
}, J = class e {
	get state() {
		return this.viewState.state;
	}
	get viewport() {
		return this.viewState.viewport;
	}
	get visibleRanges() {
		return this.viewState.visibleRanges;
	}
	get inView() {
		return this.viewState.inView;
	}
	get composing() {
		return !!this.inputState && this.inputState.composing > 0;
	}
	get compositionStarted() {
		return !!this.inputState && this.inputState.composing >= 0;
	}
	get root() {
		return this._root;
	}
	get win() {
		return this.dom.ownerDocument.defaultView || window;
	}
	constructor(e = {}) {
		var t;
		this.plugins = [], this.pluginMap = /* @__PURE__ */ new Map(), this.editorAttrs = {}, this.contentAttrs = {}, this.bidiCache = [], this.destroyed = !1, this.updateState = 2, this.measureScheduled = -1, this.measureRequests = [], this.contentDOM = document.createElement("div"), this.scrollDOM = document.createElement("div"), this.scrollDOM.tabIndex = -1, this.scrollDOM.className = "cm-scroller", this.scrollDOM.appendChild(this.contentDOM), this.announceDOM = document.createElement("div"), this.announceDOM.className = "cm-announced", this.announceDOM.setAttribute("aria-live", "polite"), this.dom = document.createElement("div"), this.dom.appendChild(this.announceDOM), this.dom.appendChild(this.scrollDOM), e.parent && e.parent.appendChild(this.dom);
		let { dispatch: n } = e;
		this.dispatchTransactions = e.dispatchTransactions || n && ((e) => e.forEach((e) => n(e, this))) || ((e) => this.update(e)), this.dispatch = this.dispatch.bind(this), this._root = e.root || dr(e.parent) || document, this.viewState = new Lo(this, e.state || N.create(e)), e.scrollTo && e.scrollTo.is(Zr) && (this.viewState.scrollTarget = e.scrollTo.value.clip(this.viewState.state)), this.plugins = this.state.facet(ti).map((e) => new ni(e));
		for (let e of this.plugins) e.update(this);
		this.observer = new rs(this), this.inputState = new ka(this), this.inputState.ensureHandlers(this.plugins), this.docView = new Ui(this), this.mountStyles(), this.updateAttrs(), this.updateState = 0, this.requestMeasure(), (t = document.fonts) != null && t.ready && document.fonts.ready.then(() => {
			this.viewState.mustMeasureContent = "refresh", this.requestMeasure();
		});
	}
	dispatch(...e) {
		let t = e.length == 1 && e[0] instanceof j ? e : e.length == 1 && Array.isArray(e[0]) ? e[0] : [this.state.update(...e)];
		this.dispatchTransactions(t, this);
	}
	update(t) {
		if (this.updateState != 0) throw Error("Calls to EditorView.update are not allowed while an update is in progress");
		let n = !1, r = !1, i, a = this.state;
		for (let e of t) {
			if (e.startState != a) throw RangeError("Trying to update state with a transaction that doesn't start from the previous state.");
			a = e.state;
		}
		if (this.destroyed) {
			this.viewState.state = a;
			return;
		}
		let o = this.hasFocus, s = 0, c = null;
		t.some((e) => e.annotation(so)) ? (this.inputState.notifiedFocused = o, s = 1) : o != this.inputState.notifiedFocused && (this.inputState.notifiedFocused = o, c = co(a, o), c || (s = 1));
		let l = this.observer.delayedAndroidKey, u = null;
		if (l ? (this.observer.clearDelayedAndroidKey(), u = this.observer.readChange(), (u && !this.state.doc.eq(a.doc) || !this.state.selection.eq(a.selection)) && (u = null)) : this.observer.clear(), a.facet(N.phrases) != this.state.facet(N.phrases)) return this.setState(a);
		i = hi.create(this, a, t), i.flags |= s;
		let d = this.viewState.scrollTarget;
		try {
			this.updateState = 2;
			for (let n of t) {
				if (d && (d = d.map(n.changes)), n.scrollIntoView) {
					let { main: t } = n.state.selection, { x: r, y: i } = this.state.facet(e.cursorScrollMargin);
					d = new Xr(t.empty ? t : D.cursor(t.head, t.head > t.anchor ? -1 : 1), "nearest", "nearest", i, r);
				}
				for (let e of n.effects) e.is(Zr) && (d = e.value.clip(this.state));
			}
			this.viewState.update(i, d), this.bidiCache = us.update(this.bidiCache, i.changes), i.empty || (this.updatePlugins(i), this.inputState.update(i)), n = this.docView.update(i), this.state.facet(pi) != this.styleModules && this.mountStyles(), r = this.updateAttrs(), this.showAnnouncements(t), this.docView.updateSelection(n, t.some((e) => e.isUserEvent("select.pointer")));
		} finally {
			this.updateState = 0;
		}
		if (i.startState.facet(qo) != i.state.facet(qo) && (this.viewState.mustMeasureContent = !0), (n || r || d || this.viewState.mustEnforceCursorAssoc || this.viewState.mustMeasureContent) && this.requestMeasure(), n && this.docViewUpdate(), !i.empty) for (let e of this.state.facet(Hr)) try {
			e(i);
		} catch (e) {
			U(this.state, e, "update listener");
		}
		(c || u) && Promise.resolve().then(() => {
			c && this.state == c.startState && this.dispatch(c), u && !Sa(this, u) && l.force && ur(this.contentDOM, l.key, l.keyCode);
		});
	}
	setState(e) {
		if (this.updateState != 0) throw Error("Calls to EditorView.setState are not allowed while an update is in progress");
		if (this.destroyed) {
			this.viewState.state = e;
			return;
		}
		this.updateState = 2;
		let t = this.hasFocus;
		try {
			for (let e of this.plugins) e.destroy(this);
			this.viewState = new Lo(this, e), this.plugins = e.facet(ti).map((e) => new ni(e)), this.pluginMap.clear();
			for (let e of this.plugins) e.update(this);
			this.docView.destroy(), this.docView = new Ui(this), this.inputState.ensureHandlers(this.plugins), this.mountStyles(), this.updateAttrs(), this.bidiCache = [];
		} finally {
			this.updateState = 0;
		}
		t && this.focus(), this.requestMeasure();
	}
	updatePlugins(e) {
		let t = e.startState.facet(ti), n = e.state.facet(ti);
		if (t != n) {
			let r = [];
			for (let i of n) {
				let n = t.indexOf(i);
				if (n < 0) r.push(new ni(i));
				else {
					let t = this.plugins[n];
					t.mustUpdate = e, r.push(t);
				}
			}
			for (let t of this.plugins) t.mustUpdate != e && t.destroy(this);
			this.plugins = r, this.pluginMap.clear();
		} else for (let t of this.plugins) t.mustUpdate = e;
		for (let e = 0; e < this.plugins.length; e++) this.plugins[e].update(this);
		t != n && this.inputState.ensureHandlers(this.plugins);
	}
	docViewUpdate() {
		for (let e of this.plugins) {
			let t = e.value;
			if (t && t.docViewUpdate) try {
				t.docViewUpdate(this);
			} catch (e) {
				U(this.state, e, "doc view update listener");
			}
		}
	}
	measure(e = !0) {
		if (this.destroyed) return;
		if (this.measureScheduled > -1 && this.win.cancelAnimationFrame(this.measureScheduled), this.observer.delayedAndroidKey) {
			this.measureScheduled = -1, this.requestMeasure();
			return;
		}
		this.measureScheduled = 0, e && this.observer.forceFlush();
		let t = null, n = this.viewState.scrollParent, r = this.viewState.getScrollOffset(), { scrollAnchorPos: i, scrollAnchorHeight: a } = this.viewState;
		Math.abs(r - this.viewState.scrollOffset) > 1 && (a = -1), this.viewState.scrollAnchorHeight = -1;
		try {
			for (let e = 0;; e++) {
				if (a < 0) {
					if (pr(n || this.win)) i = -1, a = this.viewState.heightMap.height;
					else {
						let e = this.viewState.scrollAnchorAt(r);
						i = e.from, a = e.top;
					}
				}
				this.updateState = 1;
				let o = this.viewState.measure();
				if (!o && !this.measureRequests.length && this.viewState.scrollTarget == null) break;
				if (e > 5) {
					console.warn(this.measureRequests.length ? "Measure loop restarted more than 5 times" : "Viewport failed to stabilize");
					break;
				}
				let s = [];
				o & 4 || ([this.measureRequests, s] = [s, this.measureRequests]);
				let c = s.map((e) => {
					try {
						return e.read(this);
					} catch (e) {
						return U(this.state, e), ls;
					}
				}), l = hi.create(this, this.state, []), u = !1;
				l.flags |= o, t ? t.flags |= o : t = l, this.updateState = 2, l.empty || (this.updatePlugins(l), this.inputState.update(l), this.updateAttrs(), u = this.docView.update(l), u && this.docViewUpdate());
				for (let e = 0; e < s.length; e++) if (c[e] != ls) try {
					let t = s[e];
					t.write && t.write(c[e], this);
				} catch (e) {
					U(this.state, e);
				}
				if (u && this.docView.updateSelection(!0), !l.viewportChanged && this.measureRequests.length == 0) {
					if (this.viewState.editorHeight) {
						if (this.viewState.scrollTarget) {
							this.docView.scrollIntoView(this.viewState.scrollTarget), this.viewState.scrollTarget = null, a = -1;
							continue;
						}
						{
							let e = ((i < 0 ? this.viewState.heightMap.height : this.viewState.lineBlockAt(i).top) - a) / this.scaleY;
							if ((e > 1 || e < -1) && !(R.ios && this.inputState.lastIOSMomentumScroll > Date.now() - 100) && (n == this.scrollDOM || this.hasFocus || Math.max(this.inputState.lastWheelEvent, this.inputState.lastTouchTime) > Date.now() - 100)) {
								r += e, n ? i < 0 ? n.scrollTop = n.scrollHeight : n.scrollTop += e : this.win.scrollBy(0, e), a = -1;
								continue;
							}
						}
					}
					break;
				}
			}
		} finally {
			this.updateState = 0, this.measureScheduled = -1;
		}
		if (t && !t.empty) for (let e of this.state.facet(Hr)) e(t);
	}
	get themeClasses() {
		return Yo + " " + (this.state.facet(Jo) ? Zo : Xo) + " " + this.state.facet(qo);
	}
	updateAttrs() {
		let e = ds(this, ri, { class: "cm-editor" + (this.hasFocus ? " cm-focused " : " ") + this.themeClasses }), t = {
			spellcheck: "false",
			autocorrect: "off",
			autocapitalize: "off",
			writingsuggestions: "false",
			translate: "no",
			contenteditable: this.state.facet($r) ? "true" : "false",
			class: "cm-content",
			style: `${R.tabSize}: ${this.state.tabSize}`,
			role: "textbox",
			"aria-multiline": "true"
		};
		this.state.readOnly && (t["aria-readonly"] = "true"), ds(this, ii, t);
		let n = this.observer.ignore(() => {
			let n = Nn(this.contentDOM, this.contentAttrs, t), r = Nn(this.dom, this.editorAttrs, e);
			return n || r;
		});
		return this.editorAttrs = e, this.contentAttrs = t, n;
	}
	showAnnouncements(t) {
		let n = !0;
		for (let r of t) for (let t of r.effects) if (t.is(e.announce)) {
			n && (this.announceDOM.textContent = ""), n = !1;
			let e = this.announceDOM.appendChild(document.createElement("div"));
			e.textContent = t.value;
		}
	}
	mountStyles() {
		this.styleModules = this.state.facet(pi);
		let t = this.state.facet(e.cspNonce);
		nn.mount(this.root, this.styleModules.concat(es).reverse(), t ? { nonce: t } : void 0);
	}
	readMeasured() {
		if (this.updateState == 2) throw Error("Reading the editor layout isn't allowed during an update");
		this.updateState == 0 && this.measureScheduled > -1 && this.measure(!1);
	}
	requestMeasure(e) {
		if (this.measureScheduled < 0 && (this.measureScheduled = this.win.requestAnimationFrame(() => this.measure())), e) {
			if (this.measureRequests.indexOf(e) > -1) return;
			if (e.key != null) {
				for (let t = 0; t < this.measureRequests.length; t++) if (this.measureRequests[t].key === e.key) {
					this.measureRequests[t] = e;
					return;
				}
			}
			this.measureRequests.push(e);
		}
	}
	plugin(e) {
		let t = this.pluginMap.get(e);
		return (t === void 0 || t && t.plugin != e) && this.pluginMap.set(e, t = this.plugins.find((t) => t.plugin == e) || null), t && t.update(this).value;
	}
	get documentTop() {
		return this.contentDOM.getBoundingClientRect().top + this.viewState.paddingTop;
	}
	get documentPadding() {
		return {
			top: this.viewState.paddingTop,
			bottom: this.viewState.paddingBottom
		};
	}
	get scaleX() {
		return this.viewState.scaleX;
	}
	get scaleY() {
		return this.viewState.scaleY;
	}
	elementAtHeight(e) {
		return this.readMeasured(), this.viewState.elementAtHeight(e);
	}
	lineBlockAtHeight(e) {
		return this.readMeasured(), this.viewState.lineBlockAtHeight(e);
	}
	get viewportLineBlocks() {
		return this.viewState.viewportLines;
	}
	lineBlockAt(e) {
		return this.viewState.lineBlockAt(e);
	}
	get contentHeight() {
		return this.viewState.contentHeight;
	}
	moveByChar(e, t, n) {
		return da(this, e, oa(this, e, t, n));
	}
	moveByGroup(e, t) {
		return da(this, e, oa(this, e, t, (t) => sa(this, e.head, t)));
	}
	visualLineSide(e, t) {
		let n = this.bidiSpans(e), r = this.textDirectionAt(e.from), i = n[t ? n.length - 1 : 0];
		return D.cursor(i.side(t, r) + e.from, i.forward(!t, r) ? 1 : -1);
	}
	moveToLineBoundary(e, t, n = !0) {
		return aa(this, e, t, n);
	}
	moveVertically(e, t, n) {
		return da(this, e, ca(this, e, t, n));
	}
	domAtPos(e, t = 1) {
		return this.docView.domAtPos(e, t);
	}
	posAtDOM(e, t = 0) {
		return this.docView.posFromDOM(e, t);
	}
	posAtCoords(e, t = !0) {
		this.readMeasured();
		let n = pa(this, e, t);
		return n && n.pos;
	}
	posAndSideAtCoords(e, t = !0) {
		return this.readMeasured(), pa(this, e, t);
	}
	coordsAtPos(e, t = 1) {
		this.readMeasured();
		let n = this.state.doc.lineAt(e), r = this.bidiSpans(n), i = r[Er.find(r, e - n.from, -1, t)];
		return this.docView.coordsAt(e, t, i.dir == V.RTL);
	}
	coordsForChar(e) {
		return this.readMeasured(), this.docView.coordsForChar(e);
	}
	get defaultCharacterWidth() {
		return this.viewState.heightOracle.charWidth;
	}
	get defaultLineHeight() {
		return this.viewState.heightOracle.lineHeight;
	}
	get textDirection() {
		return this.viewState.defaultTextDirection;
	}
	textDirectionAt(e) {
		return !this.state.facet(qr) || e < this.viewport.from || e > this.viewport.to ? this.textDirection : (this.readMeasured(), this.docView.textDirectionAt(e));
	}
	get lineWrapping() {
		return this.viewState.heightOracle.lineWrapping;
	}
	bidiSpans(e) {
		if (e.length > cs) return Pr(e.length);
		let t = this.textDirectionAt(e.from), n;
		for (let r of this.bidiCache) if (r.from == e.from && r.dir == t && (r.fresh || Dr(r.isolates, n = ui(this, e)))) return r.order;
		n || (n = ui(this, e));
		let r = Nr(e.text, t, n);
		return this.bidiCache.push(new us(e.from, e.to, t, n, !0, r)), r;
	}
	get hasFocus() {
		var e;
		return (this.dom.ownerDocument.hasFocus() || R.safari && ((e = this.inputState) == null ? void 0 : e.lastContextMenu) > Date.now() - 3e4) && this.root.activeElement == this.contentDOM;
	}
	focus() {
		this.observer.ignore(() => {
			sr(this.contentDOM), this.docView.updateSelection();
		});
	}
	setRoot(e) {
		this._root != e && (this._root = e, this.observer.setWindow((e.nodeType == 9 ? e : e.ownerDocument).defaultView || window), this.mountStyles());
	}
	destroy() {
		this.root.activeElement == this.contentDOM && this.contentDOM.blur();
		for (let e of this.plugins) e.destroy(this);
		this.plugins = [], this.inputState.destroy(), this.docView.destroy(), this.dom.remove(), this.observer.destroy(), this.measureScheduled > -1 && this.win.cancelAnimationFrame(this.measureScheduled), this.destroyed = !0;
	}
	static scrollIntoView(e, t = {}) {
		var n, r, i, a;
		return Zr.of(new Xr(typeof e == "number" ? D.cursor(e) : e, (n = t.y) == null ? "nearest" : n, (r = t.x) == null ? "nearest" : r, (i = t.yMargin) == null ? 5 : i, (a = t.xMargin) == null ? 5 : a));
	}
	scrollSnapshot() {
		let { scrollTop: e, scrollLeft: t } = this.scrollDOM, n = this.viewState.scrollAnchorAt(e);
		return Zr.of(new Xr(D.cursor(n.from), "start", "start", n.top - e, t, !0));
	}
	setTabFocusMode(e) {
		e == null ? this.inputState.tabFocusMode = this.inputState.tabFocusMode < 0 ? 0 : -1 : typeof e == "boolean" ? this.inputState.tabFocusMode = e ? 0 : -1 : this.inputState.tabFocusMode != 0 && (this.inputState.tabFocusMode = Date.now() + e);
	}
	static domEventHandlers(e) {
		return W.define(() => ({}), { eventHandlers: e });
	}
	static domEventObservers(e) {
		return W.define(() => ({}), { eventObservers: e });
	}
	static theme(e, t) {
		let n = nn.newName(), r = [qo.of(n), pi.of($o(`.${n}`, e))];
		return t && t.dark && r.push(Jo.of(!0)), r;
	}
	static baseTheme(e) {
		return nt.lowest(pi.of($o("." + Yo, e, Qo)));
	}
	static findFromDOM(e) {
		var t;
		let n = e.querySelector(".cm-content"), r = n && G.get(n) || G.get(e);
		return ((t = r == null ? void 0 : r.root) == null ? void 0 : t.view) || null;
	}
};
J.styleModule = pi, J.inputHandler = Ur, J.clipboardInputFilter = Gr, J.clipboardOutputFilter = Kr, J.scrollHandler = Yr, J.focusChangeEffect = Wr, J.perLineTextDirection = qr, J.exceptionSink = Vr, J.updateListener = Hr, J.editable = $r, J.mouseSelectionStyle = Br, J.dragMovesSelection = zr, J.clickAddsSelectionRange = Rr, J.decorations = ai, J.blockWrappers = oi, J.outerDecorations = si, J.atomicRanges = ci, J.bidiIsolatedRanges = li, J.cursorScrollMargin = /*@__PURE__*/ O.define({ combine: (e) => {
	let t = 5, n = 5;
	for (let r of e) typeof r == "number" ? t = n = r : {x: t, y: n} = r;
	return {
		x: t,
		y: n
	};
} }), J.scrollMargins = di, J.darkTheme = Jo, J.cspNonce = /*@__PURE__*/ O.define({ combine: (e) => e.length ? e[0] : "" }), J.contentAttributes = ii, J.editorAttributes = ri, J.lineWrapping = /*@__PURE__*/ J.contentAttributes.of({ class: "cm-lineWrapping" }), J.announce = /*@__PURE__*/ A.define();
var cs = 4096, ls = {}, us = class e {
	constructor(e, t, n, r, i, a) {
		this.from = e, this.to = t, this.dir = n, this.isolates = r, this.fresh = i, this.order = a;
	}
	static update(t, n) {
		if (n.empty && !t.some((e) => e.fresh)) return t;
		let r = [], i = t.length ? t[t.length - 1].dir : V.LTR;
		for (let a = Math.max(0, t.length - 10); a < t.length; a++) {
			let o = t[a];
			o.dir == i && !n.touchesRange(o.from, o.to) && r.push(new e(n.mapPos(o.from, 1), n.mapPos(o.to, -1), o.dir, o.isolates, !1, o.order));
		}
		return r;
	}
};
function ds(e, t, n) {
	for (let r = e.state.facet(t), i = r.length - 1; i >= 0; i--) {
		let t = r[i], a = typeof t == "function" ? t(e) : t;
		a && kn(a, n);
	}
	return n;
}
var fs = R.mac ? "mac" : R.windows ? "win" : R.linux ? "linux" : "key";
function ps(e, t) {
	let n = e.split(/-(?!$)/), r = n[n.length - 1];
	r == "Space" && (r = " ");
	let i, a, o, s;
	for (let e = 0; e < n.length - 1; ++e) {
		let r = n[e];
		if (/^(cmd|meta|m)$/i.test(r)) s = !0;
		else if (/^a(lt)?$/i.test(r)) i = !0;
		else if (/^(c|ctrl|control)$/i.test(r)) a = !0;
		else if (/^s(hift)?$/i.test(r)) o = !0;
		else if (/^mod$/i.test(r)) t == "mac" ? s = !0 : a = !0;
		else throw Error("Unrecognized modifier name: " + r);
	}
	return i && (r = "Alt-" + r), a && (r = "Ctrl-" + r), s && (r = "Meta-" + r), o && (r = "Shift-" + r), r;
}
function ms(e, t, n) {
	return t.altKey && (e = "Alt-" + e), t.ctrlKey && (e = "Ctrl-" + e), t.metaKey && (e = "Meta-" + e), n !== !1 && t.shiftKey && (e = "Shift-" + e), e;
}
var hs = /*@__PURE__*/ nt.default(/*@__PURE__*/ J.domEventHandlers({ keydown(e, t) {
	return ws(vs(t.state), e, t, "editor");
} })), gs = /*@__PURE__*/ O.define({ enables: hs }), _s = /*@__PURE__*/ new WeakMap();
function vs(e) {
	let t = e.facet(gs), n = _s.get(t);
	return n || _s.set(t, n = Ss(t.reduce((e, t) => e.concat(t), []))), n;
}
function ys(e, t, n) {
	return ws(vs(e.state), t, e, n);
}
var bs = null, xs = 4e3;
function Ss(e, t = fs) {
	let n = Object.create(null), r = Object.create(null), i = (e, t) => {
		let n = r[e];
		if (n == null) r[e] = t;
		else if (n != t) throw Error("Key binding " + e + " is used both as a regular binding and as a multi-stroke prefix");
	}, a = (e, r, a, o, s) => {
		var c, l;
		let u = n[e] || (n[e] = Object.create(null)), d = r.split(/ (?!$)/).map((e) => ps(e, t));
		for (let t = 1; t < d.length; t++) {
			let n = d.slice(0, t).join(" ");
			i(n, !0), u[n] || (u[n] = {
				preventDefault: !0,
				stopPropagation: !1,
				run: [(t) => {
					let r = bs = {
						view: t,
						prefix: n,
						scope: e
					};
					return setTimeout(() => {
						bs == r && (bs = null);
					}, xs), !0;
				}]
			});
		}
		let f = d.join(" ");
		i(f, !1);
		let p = u[f] || (u[f] = {
			preventDefault: !1,
			stopPropagation: !1,
			run: ((l = (c = u._any) == null ? void 0 : c.run) == null ? void 0 : l.slice()) || []
		});
		a && p.run.push(a), o && (p.preventDefault = !0), s && (p.stopPropagation = !0);
	};
	for (let r of e) {
		let e = r.scope ? r.scope.split(" ") : ["editor"];
		if (r.any) for (let t of e) {
			let e = n[t] || (n[t] = Object.create(null));
			e._any || (e._any = {
				preventDefault: !1,
				stopPropagation: !1,
				run: []
			});
			let { any: i } = r;
			for (let t in e) e[t].run.push((e) => i(e, Cs));
		}
		let i = r[t] || r.key;
		if (i) for (let t of e) a(t, i, r.run, r.preventDefault, r.stopPropagation), r.shift && a(t, "Shift-" + i, r.shift, r.preventDefault, r.stopPropagation);
	}
	return n;
}
var Cs = null;
function ws(e, t, n, r) {
	Cs = t;
	let i = dn(t), a = Ie(Pe(i, 0)) == i.length && i != " ", o = "", s = !1, c = !1, l = !1;
	bs && bs.view == n && bs.scope == r && (o = bs.prefix + " ", Fa.indexOf(t.keyCode) < 0 && (c = !0, bs = null));
	let u = /* @__PURE__ */ new Set(), d = (e) => {
		if (e) {
			for (let t of e.run) if (!u.has(t) && (u.add(t), t(n))) return e.stopPropagation && (l = !0), !0;
			e.preventDefault && (e.stopPropagation && (l = !0), c = !0);
		}
		return !1;
	}, f = e[r], p, m;
	return f && (d(f[o + ms(i, t, !a)]) ? s = !0 : a && (t.altKey || t.metaKey || t.ctrlKey) && !(R.windows && t.ctrlKey && t.altKey) && !(R.mac && t.altKey && !(t.ctrlKey || t.metaKey)) && (p = on[t.keyCode]) && p != i ? (d(f[o + ms(p, t, !0)]) || t.shiftKey && (m = sn[t.keyCode]) != i && m != p && d(f[o + ms(m, t, !1)])) && (s = !0) : a && t.shiftKey && d(f[o + ms(i, t, !0)]) && (s = !0), !s && d(f._any) && (s = !0)), c && (s = !0), s && l && t.stopPropagation(), Cs = null, s;
}
var Ts = class e {
	constructor(e, t, n, r, i) {
		this.className = e, this.left = t, this.top = n, this.width = r, this.height = i;
	}
	draw() {
		let e = document.createElement("div");
		return e.className = this.className, this.adjust(e), e;
	}
	update(e, t) {
		return t.className == this.className && (this.adjust(e), !0);
	}
	adjust(e) {
		e.style.left = this.left + "px", e.style.top = this.top + "px", this.width != null && (e.style.width = this.width + "px"), e.style.height = this.height + "px";
	}
	eq(e) {
		return this.left == e.left && this.top == e.top && this.width == e.width && this.height == e.height && this.className == e.className;
	}
	static forRange(t, n, r) {
		if (r.empty) {
			let i = t.coordsAtPos(r.head, r.assoc || 1);
			if (!i) return [];
			let a = Es(t);
			return [new e(n, i.left - a.left, i.top - a.top, null, i.bottom - i.top)];
		}
		return Os(t, n, r);
	}
};
function Es(e) {
	let t = e.scrollDOM.getBoundingClientRect();
	return {
		left: (e.textDirection == V.LTR ? t.left : t.right - e.scrollDOM.clientWidth * e.scaleX) - e.scrollDOM.scrollLeft * e.scaleX,
		top: t.top - e.scrollDOM.scrollTop * e.scaleY
	};
}
function Ds(e, t, n, r) {
	let i = e.coordsAtPos(t, n * 2);
	if (!i) return r;
	let a = e.dom.getBoundingClientRect(), o = (i.top + i.bottom) / 2, s = e.posAtCoords({
		x: a.left + 1,
		y: o
	}), c = e.posAtCoords({
		x: a.right - 1,
		y: o
	});
	return s == null || c == null ? r : {
		from: Math.max(r.from, Math.min(s, c)),
		to: Math.min(r.to, Math.max(s, c))
	};
}
function Os(e, t, n) {
	if (n.to <= e.viewport.from || n.from >= e.viewport.to) return [];
	let r = Math.max(n.from, e.viewport.from), i = Math.min(n.to, e.viewport.to), a = e.textDirection == V.LTR, o = e.contentDOM, s = o.getBoundingClientRect(), c = Es(e), l = o.querySelector(".cm-line"), u = l && window.getComputedStyle(l), d = s.left + (u ? parseInt(u.paddingLeft) + Math.min(0, parseInt(u.textIndent)) : 0), f = s.right - (u ? parseInt(u.paddingRight) : 0), p = ia(e, r, 1), m = ia(e, i, -1), h = p.type == z.Text ? p : null, g = m.type == z.Text ? m : null;
	if (h && (e.lineWrapping || p.widgetLineBreaks) && (h = Ds(e, r, 1, h)), g && (e.lineWrapping || m.widgetLineBreaks) && (g = Ds(e, i, -1, g)), h && g && h.from == g.from && h.to == g.to) return v(y(n.from, n.to, h));
	{
		let t = h ? y(n.from, null, h) : b(p, !1), r = g ? y(null, n.to, g) : b(m, !0), i = [];
		return (h || p).to < (g || m).from - (h && g ? 1 : 0) || p.widgetLineBreaks > 1 && t.bottom + e.defaultLineHeight / 2 < r.top ? i.push(_(d, t.bottom, f, r.top)) : t.bottom < r.top && e.elementAtHeight((t.bottom + r.top) / 2).type == z.Text && (t.bottom = r.top = (t.bottom + r.top) / 2), v(t).concat(i).concat(v(r));
	}
	function _(e, n, r, i) {
		return new Ts(t, e - c.left, n - c.top, Math.max(0, r - e), i - n);
	}
	function v({ top: e, bottom: t, horizontal: n }) {
		let r = [];
		for (let i = 0; i < n.length; i += 2) r.push(_(n[i], e, n[i + 1], t));
		return r;
	}
	function y(t, n, r) {
		let i = 1e9, o = -1e9, s = [];
		function c(t, n, c, l, u) {
			let p = e.coordsAtPos(t, t == r.to ? -2 : 2), m = e.coordsAtPos(c, c == r.from ? 2 : -2);
			!p || !m || (i = Math.min(p.top, m.top, i), o = Math.max(p.bottom, m.bottom, o), u == V.LTR ? s.push(a && n ? d : p.left, a && l ? f : m.right) : s.push(!a && l ? d : m.left, !a && n ? f : p.right));
		}
		let l = t == null ? r.from : t, u = n == null ? r.to : n;
		for (let r of e.visibleRanges) if (r.to > l && r.from < u) for (let i = Math.max(r.from, l), a = Math.min(r.to, u);;) {
			let r = e.state.doc.lineAt(i);
			for (let o of e.bidiSpans(r)) {
				let e = o.from + r.from, s = o.to + r.from;
				if (e >= a) break;
				s > i && c(Math.max(e, i), t == null && e <= l, Math.min(s, a), n == null && s >= u, o.dir);
			}
			if (i = r.to + 1, i >= a) break;
		}
		return s.length == 0 && c(l, t == null, u, n == null, e.textDirection), {
			top: i,
			bottom: o,
			horizontal: s
		};
	}
	function b(e, t) {
		let n = s.top + (t ? e.top : e.bottom);
		return {
			top: n,
			bottom: n,
			horizontal: []
		};
	}
}
function ks(e, t) {
	return e.constructor == t.constructor && e.eq(t);
}
var As = class {
	constructor(e, t) {
		this.view = e, this.layer = t, this.drawn = [], this.scaleX = 1, this.scaleY = 1, this.measureReq = {
			read: this.measure.bind(this),
			write: this.draw.bind(this)
		}, this.dom = e.scrollDOM.appendChild(document.createElement("div")), this.dom.classList.add("cm-layer"), t.above && this.dom.classList.add("cm-layer-above"), t.class && this.dom.classList.add(t.class), this.scale(), this.dom.setAttribute("aria-hidden", "true"), this.setOrder(e.state), e.requestMeasure(this.measureReq), t.mount && t.mount(this.dom, e);
	}
	update(e) {
		e.startState.facet(js) != e.state.facet(js) && this.setOrder(e.state), (this.layer.update(e, this.dom) || e.geometryChanged) && (this.scale(), e.view.requestMeasure(this.measureReq));
	}
	docViewUpdate(e) {
		this.layer.updateOnDocViewUpdate !== !1 && e.requestMeasure(this.measureReq);
	}
	setOrder(e) {
		let t = 0, n = e.facet(js);
		for (; t < n.length && n[t] != this.layer;) t++;
		this.dom.style.zIndex = String((this.layer.above ? 150 : -1) - t);
	}
	measure() {
		return this.layer.markers(this.view);
	}
	scale() {
		let { scaleX: e, scaleY: t } = this.view;
		(e != this.scaleX || t != this.scaleY) && (this.scaleX = e, this.scaleY = t, this.dom.style.transform = `scale(${1 / e}, ${1 / t})`);
	}
	draw(e) {
		if (e.length != this.drawn.length || e.some((e, t) => !ks(e, this.drawn[t]))) {
			let t = this.dom.firstChild, n = 0;
			for (let r of e) r.update && t && r.constructor && this.drawn[n].constructor && r.update(t, this.drawn[n]) ? (t = t.nextSibling, n++) : this.dom.insertBefore(r.draw(), t);
			for (; t;) {
				let e = t.nextSibling;
				t.remove(), t = e;
			}
			this.drawn = e, R.webkit && (this.dom.style.display = this.dom.firstChild ? "" : "none");
		}
	}
	destroy() {
		this.layer.destroy && this.layer.destroy(this.dom, this.view), this.dom.remove();
	}
}, js = /*@__PURE__*/ O.define();
function Ms(e) {
	return [W.define((t) => new As(t, e)), js.of(e)];
}
var Ns = /*@__PURE__*/ O.define({ combine(e) {
	return Mt(e, {
		cursorBlinkRate: 1200,
		drawRangeCursor: !0,
		iosSelectionHandles: !0
	}, {
		cursorBlinkRate: (e, t) => Math.min(e, t),
		drawRangeCursor: (e, t) => e || t
	});
} });
function Ps(e = {}) {
	return [
		Ns.of(e),
		Is,
		Rs,
		Bs,
		Jr.of(!0)
	];
}
function Fs(e) {
	return e.startState.facet(Ns) != e.state.facet(Ns);
}
var Is = /*@__PURE__*/ Ms({
	above: !0,
	markers(e) {
		let { state: t } = e, n = t.facet(Ns), r = [];
		for (let i of t.selection.ranges) {
			let a = i == t.selection.main;
			if (i.empty || n.drawRangeCursor && !(a && R.ios && n.iosSelectionHandles)) {
				let t = a ? "cm-cursor cm-cursor-primary" : "cm-cursor cm-cursor-secondary", n = i.empty ? i : D.cursor(i.head, i.assoc);
				for (let i of Ts.forRange(e, t, n)) r.push(i);
			}
		}
		return r;
	},
	update(e, t) {
		e.transactions.some((e) => e.selection) && (t.style.animationName = t.style.animationName == "cm-blink" ? "cm-blink2" : "cm-blink");
		let n = Fs(e);
		return n && Ls(e.state, t), e.docChanged || e.selectionSet || n;
	},
	mount(e, t) {
		Ls(t.state, e);
	},
	class: "cm-cursorLayer"
});
function Ls(e, t) {
	t.style.animationDuration = e.facet(Ns).cursorBlinkRate + "ms";
}
var Rs = /*@__PURE__*/ Ms({
	above: !1,
	markers(e) {
		let t = [], { main: n, ranges: r } = e.state.selection;
		for (let n of r) if (!n.empty) for (let r of Ts.forRange(e, "cm-selectionBackground", n)) t.push(r);
		if (R.ios && !n.empty && e.state.facet(Ns).iosSelectionHandles) {
			for (let r of Ts.forRange(e, "cm-selectionHandle cm-selectionHandle-start", D.cursor(n.from, 1))) t.push(r);
			for (let r of Ts.forRange(e, "cm-selectionHandle cm-selectionHandle-end", D.cursor(n.to, 1))) t.push(r);
		}
		return t;
	},
	update(e, t) {
		return e.docChanged || e.selectionSet || e.viewportChanged || Fs(e);
	},
	class: "cm-selectionLayer"
}), zs = R.gecko && R.gecko_version == 153 ? "#ffffff01" : "transparent", Bs = /*@__PURE__*/ nt.highest(/*@__PURE__*/ J.theme({
	".cm-line": {
		"& ::selection, &::selection": { backgroundColor: `${zs} !important` },
		caretColor: "transparent !important"
	},
	".cm-content": {
		caretColor: "transparent !important",
		"& :focus": {
			caretColor: "initial !important",
			"&::selection, & ::selection": { backgroundColor: "Highlight !important" }
		}
	}
})), Vs = /*@__PURE__*/ A.define({ map(e, t) {
	return e == null ? null : t.mapPos(e);
} }), Hs = /*@__PURE__*/ k.define({
	create() {
		return null;
	},
	update(e, t) {
		return e != null && (e = t.changes.mapPos(e)), t.effects.reduce((e, t) => t.is(Vs) ? t.value : e, e);
	}
}), Us = /*@__PURE__*/ W.fromClass(class {
	constructor(e) {
		this.view = e, this.cursor = null, this.measureReq = {
			read: this.readPos.bind(this),
			write: this.drawCursor.bind(this)
		};
	}
	update(e) {
		var t;
		let n = e.state.field(Hs);
		n == null ? this.cursor != null && ((t = this.cursor) == null || t.remove(), this.cursor = null) : (this.cursor || (this.cursor = this.view.scrollDOM.appendChild(document.createElement("div")), this.cursor.className = "cm-dropCursor"), (e.startState.field(Hs) != n || e.docChanged || e.geometryChanged) && this.view.requestMeasure(this.measureReq));
	}
	readPos() {
		let { view: e } = this, t = e.state.field(Hs), n = t != null && e.coordsAtPos(t);
		if (!n) return null;
		let r = e.scrollDOM.getBoundingClientRect();
		return {
			left: n.left - r.left + e.scrollDOM.scrollLeft * e.scaleX,
			top: n.top - r.top + e.scrollDOM.scrollTop * e.scaleY,
			height: n.bottom - n.top
		};
	}
	drawCursor(e) {
		if (this.cursor) {
			let { scaleX: t, scaleY: n } = this.view;
			e ? (this.cursor.style.left = e.left / t + "px", this.cursor.style.top = e.top / n + "px", this.cursor.style.height = e.height / n + "px") : this.cursor.style.left = "-100000px";
		}
	}
	destroy() {
		this.cursor && this.cursor.remove();
	}
	setDropPos(e) {
		this.view.state.field(Hs) != e && this.view.dispatch({ effects: Vs.of(e) });
	}
}, { eventObservers: {
	dragover(e) {
		this.setDropPos(this.view.posAtCoords({
			x: e.clientX,
			y: e.clientY
		}));
	},
	dragleave(e) {
		(e.target == this.view.contentDOM || !this.view.contentDOM.contains(e.relatedTarget)) && this.setDropPos(null);
	},
	dragend() {
		this.setDropPos(null);
	},
	drop() {
		this.setDropPos(null);
	}
} });
function Ws() {
	return [Hs, Us];
}
function Gs(e, t, n, r, i) {
	t.lastIndex = 0;
	for (let a = e.iterRange(n, r), o = n, s; !a.next().done; o += a.value.length) if (!a.lineBreak) for (; s = t.exec(a.value);) i(o + s.index, s);
}
function Ks(e, t) {
	let n = e.visibleRanges;
	if (n.length == 1 && n[0].from == e.viewport.from && n[0].to == e.viewport.to) return n;
	let r = [];
	for (let { from: i, to: a } of n) i = Math.max(e.state.doc.lineAt(i).from, i - t), a = Math.min(e.state.doc.lineAt(a).to, a + t), r.length && r[r.length - 1].to >= i ? r[r.length - 1].to = a : r.push({
		from: i,
		to: a
	});
	return r;
}
var qs = class {
	constructor(e) {
		let { regexp: t, decoration: n, decorate: r, boundary: i, maxLength: a = 1e3 } = e;
		if (!t.global) throw RangeError("The regular expression given to MatchDecorator should have its 'g' flag set");
		if (this.regexp = t, r) this.addMatch = (e, t, n, i) => r(i, n, n + e[0].length, e, t);
		else if (typeof n == "function") this.addMatch = (e, t, r, i) => {
			let a = n(e, t, r);
			a && i(r, r + e[0].length, a);
		};
		else if (n) this.addMatch = (e, t, r, i) => i(r, r + e[0].length, n);
		else throw RangeError("Either 'decorate' or 'decoration' should be provided to MatchDecorator");
		this.boundary = i, this.maxLength = a;
	}
	createDeco(e) {
		let t = new zt(), n = t.add.bind(t);
		for (let { from: t, to: r } of Ks(e, this.maxLength)) Gs(e.state.doc, this.regexp, t, r, (t, r) => this.addMatch(r, e, t, n));
		return t.finish();
	}
	updateDeco(e, t) {
		let n = 1e9, r = -1;
		return e.docChanged && e.changes.iterChanges((t, i, a, o) => {
			o >= e.view.viewport.from && a <= e.view.viewport.to && (n = Math.min(a, n), r = Math.max(o, r));
		}), e.viewportMoved || r - n > 1e3 ? this.createDeco(e.view) : r > -1 ? this.updateRange(e.view, t.map(e.changes), n, r) : t;
	}
	updateRange(e, t, n, r) {
		for (let i of e.visibleRanges) {
			let a = Math.max(i.from, n), o = Math.min(i.to, r);
			if (o >= a) {
				let n = e.state.doc.lineAt(a), r = n.to < o ? e.state.doc.lineAt(o) : n, s = Math.max(i.from, n.from), c = Math.min(i.to, r.to);
				if (this.boundary) {
					for (; a > n.from; a--) if (this.boundary.test(n.text[a - 1 - n.from])) {
						s = a;
						break;
					}
					for (; o < r.to; o++) if (this.boundary.test(r.text[o - r.from])) {
						c = o;
						break;
					}
				}
				let l = [], u, d = (e, t, n) => l.push(n.range(e, t));
				if (n == r) for (this.regexp.lastIndex = s - n.from; (u = this.regexp.exec(n.text)) && u.index < c - n.from;) this.addMatch(u, e, u.index + n.from, d);
				else Gs(e.state.doc, this.regexp, s, c, (t, n) => this.addMatch(n, e, t, d));
				t = t.update({
					filterFrom: s,
					filterTo: c,
					filter: (e, t) => e < s || t > c,
					add: l
				});
			}
		}
		return t;
	}
}, Js = /x/.unicode == null ? "g" : "gu", Ys = /*@__PURE__*/ RegExp("[\0-\b\n--­؜​‎‏\u2028\u2029‭‮⁦⁧⁩﻿￹-￼]", Js), Xs = {
	0: "null",
	7: "bell",
	8: "backspace",
	10: "newline",
	11: "vertical tab",
	13: "carriage return",
	27: "escape",
	8203: "zero width space",
	8204: "zero width non-joiner",
	8205: "zero width joiner",
	8206: "left-to-right mark",
	8207: "right-to-left mark",
	8232: "line separator",
	8237: "left-to-right override",
	8238: "right-to-left override",
	8294: "left-to-right isolate",
	8295: "right-to-left isolate",
	8297: "pop directional isolate",
	8233: "paragraph separator",
	65279: "zero width no-break space",
	65532: "object replacement"
}, Zs = null;
function Qs() {
	var e;
	if (Zs == null && typeof document < "u" && document.body) {
		let t = document.body.style;
		Zs = ((e = t.tabSize) == null ? t.MozTabSize : e) != null;
	}
	return Zs || !1;
}
var $s = /*@__PURE__*/ O.define({ combine(e) {
	let t = Mt(e, {
		render: null,
		specialChars: Ys,
		addSpecialChars: null
	});
	return (t.replaceTabs = !Qs()) && (t.specialChars = RegExp("	|" + t.specialChars.source, Js)), t.addSpecialChars && (t.specialChars = RegExp(t.specialChars.source + "|" + t.addSpecialChars.source, Js)), t;
} });
function ec(e = {}) {
	return [$s.of(e), nc()];
}
var tc = null;
function nc() {
	return tc || (tc = W.fromClass(class {
		constructor(e) {
			this.view = e, this.decorations = B.none, this.decorationCache = Object.create(null), this.decorator = this.makeDecorator(e.state.facet($s)), this.decorations = this.decorator.createDeco(e);
		}
		makeDecorator(e) {
			return new qs({
				regexp: e.specialChars,
				decoration: (t, n, r) => {
					let { doc: i } = n.state, a = Pe(t[0], 0);
					if (a == 9) {
						let e = i.lineAt(r), t = n.state.tabSize, a = Xt(e.text, t, r - e.from);
						return B.replace({ widget: new oc((t - a % t) * this.view.defaultCharacterWidth / this.view.scaleX) });
					}
					return this.decorationCache[a] || (this.decorationCache[a] = B.replace({ widget: new ac(e, a) }));
				},
				boundary: e.replaceTabs ? void 0 : /[^]/
			});
		}
		update(e) {
			let t = e.state.facet($s);
			e.startState.facet($s) == t ? this.decorations = this.decorator.updateDeco(e, this.decorations) : (this.decorator = this.makeDecorator(t), this.decorations = this.decorator.createDeco(e.view));
		}
	}, { decorations: (e) => e.decorations }));
}
var rc = "•";
function ic(e) {
	return e >= 32 ? rc : e == 10 ? "␤" : String.fromCharCode(9216 + e);
}
var ac = class extends Fn {
	constructor(e, t) {
		super(), this.options = e, this.code = t;
	}
	eq(e) {
		return e.code == this.code;
	}
	toDOM(e) {
		let t = ic(this.code), n = e.state.phrase("Control character") + " " + (Xs[this.code] || "0x" + this.code.toString(16)), r = this.options.render && this.options.render(this.code, n, t);
		if (r) return r;
		let i = document.createElement("span");
		return i.textContent = t, i.title = n, i.setAttribute("aria-label", n), i.className = "cm-specialChar", i;
	}
	ignoreEvent() {
		return !1;
	}
}, oc = class extends Fn {
	constructor(e) {
		super(), this.width = e;
	}
	eq(e) {
		return e.width == this.width;
	}
	toDOM() {
		let e = document.createElement("span");
		return e.textContent = "	", e.className = "cm-tab", e.style.width = this.width + "px", e;
	}
	ignoreEvent() {
		return !1;
	}
};
function sc() {
	return lc;
}
var cc = /*@__PURE__*/ B.line({ class: "cm-activeLine" }), lc = /*@__PURE__*/ W.fromClass(class {
	constructor(e) {
		this.decorations = this.getDeco(e);
	}
	update(e) {
		(e.docChanged || e.selectionSet) && (this.decorations = this.getDeco(e.view));
	}
	getDeco(e) {
		let t = -1, n = [];
		for (let r of e.state.selection.ranges) {
			let i = e.lineBlockAt(r.head);
			i.from > t && (n.push(cc.range(i.from)), t = i.from);
		}
		return B.set(n);
	}
}, { decorations: (e) => e.decorations }), uc = 2e3;
function dc(e, t, n) {
	let r = Math.min(t.line, n.line), i = Math.max(t.line, n.line), a = [];
	if (t.off > uc || n.off > uc || t.col < 0 || n.col < 0) {
		let o = Math.min(t.off, n.off), s = Math.max(t.off, n.off);
		for (let t = r; t <= i; t++) {
			let n = e.doc.line(t);
			n.length <= s && a.push(D.range(n.from + o, n.to + s));
		}
	} else {
		let o = Math.min(t.col, n.col), s = Math.max(t.col, n.col);
		for (let t = r; t <= i; t++) {
			let n = e.doc.line(t), r = Zt(n.text, o, e.tabSize, !0);
			if (r < 0) a.push(D.cursor(n.to));
			else {
				let t = Zt(n.text, s, e.tabSize);
				a.push(D.range(n.from + r, n.from + t));
			}
		}
	}
	return a;
}
function fc(e, t) {
	let n = e.coordsAtPos(e.viewport.from);
	return n ? Math.round(Math.abs((n.left - t) / e.defaultCharacterWidth)) : -1;
}
function pc(e, t) {
	let n = e.posAtCoords({
		x: t.clientX,
		y: t.clientY
	}, !1), r = e.state.doc.lineAt(n), i = n - r.from, a = i > uc ? -1 : i == r.length ? fc(e, t.clientX) : Xt(r.text, e.state.tabSize, n - r.from);
	return {
		line: r.number,
		col: a,
		off: i
	};
}
function mc(e, t) {
	let n = pc(e, t), r = e.state.selection;
	return n ? {
		update(e) {
			if (e.docChanged) {
				let t = e.changes.mapPos(e.startState.doc.line(n.line).from), i = e.state.doc.lineAt(t);
				n = {
					line: i.number,
					col: n.col,
					off: Math.min(n.off, i.length)
				}, r = r.map(e.changes);
			}
		},
		get(t, i, a) {
			let o = pc(e, t);
			if (!o) return r;
			let s = dc(e.state, n, o);
			return s.length ? a ? D.create(s.concat(r.ranges)) : D.create(s) : r;
		}
	} : null;
}
function hc(e) {
	let t = (e == null ? void 0 : e.eventFilter) || ((e) => e.altKey && e.button == 0);
	return J.mouseSelectionStyle.of((e, n) => t(n) ? mc(e, n) : null);
}
var gc = {
	Alt: [18, (e) => !!e.altKey],
	Control: [17, (e) => !!e.ctrlKey],
	Shift: [16, (e) => !!e.shiftKey],
	Meta: [91, (e) => !!e.metaKey]
}, _c = { style: "cursor: crosshair" };
function vc(e = {}) {
	let [t, n] = gc[e.key || "Alt"], r = W.fromClass(class {
		constructor(e) {
			this.view = e, this.isDown = !1;
		}
		set(e) {
			this.isDown != e && (this.isDown = e, this.view.update([]));
		}
	}, { eventObservers: {
		keydown(e) {
			this.set(e.keyCode == t || n(e));
		},
		keyup(e) {
			(e.keyCode == t || !n(e)) && this.set(!1);
		},
		mousemove(e) {
			this.set(n(e));
		}
	} });
	return [r, J.contentAttributes.of((e) => {
		var t;
		return (t = e.plugin(r)) != null && t.isDown ? _c : null;
	})];
}
var yc = "-10000px", bc = class {
	constructor(e, t, n, r) {
		this.facet = t, this.createTooltipView = n, this.removeTooltipView = r, this.input = e.state.facet(t), this.tooltips = this.input.filter((e) => e);
		let i = null;
		this.tooltipViews = this.tooltips.map((e) => i = n(e, i));
	}
	update(e, t) {
		var n;
		let r = e.state.facet(this.facet), i = r.filter((e) => e);
		if (r === this.input) {
			for (let t of this.tooltipViews) t.update && t.update(e);
			return !1;
		}
		let a = [], o = t ? [] : null;
		for (let n = 0; n < i.length; n++) {
			let r = i[n], s = -1;
			if (r) {
				for (let e = 0; e < this.tooltips.length; e++) {
					let t = this.tooltips[e];
					t && t.create == r.create && (s = e);
				}
				if (s < 0) a[n] = this.createTooltipView(r, n ? a[n - 1] : null), o && (o[n] = !!r.above);
				else {
					let r = a[n] = this.tooltipViews[s];
					o && (o[n] = t[s]), r.update && r.update(e);
				}
			}
		}
		for (let e of this.tooltipViews) a.indexOf(e) < 0 && (this.removeTooltipView(e), (n = e.destroy) == null || n.call(e));
		return t && (o.forEach((e, n) => t[n] = e), t.length = o.length), this.input = r, this.tooltips = i, this.tooltipViews = a, !0;
	}
};
function xc(e) {
	let t = e.dom.ownerDocument.documentElement;
	return {
		top: 0,
		left: 0,
		bottom: t.clientHeight,
		right: t.clientWidth
	};
}
var Sc = /*@__PURE__*/ O.define({ combine: (e) => {
	var t, n, r;
	return {
		position: R.ios ? "absolute" : ((t = e.find((e) => e.position)) == null ? void 0 : t.position) || "fixed",
		parent: ((n = e.find((e) => e.parent)) == null ? void 0 : n.parent) || null,
		tooltipSpace: ((r = e.find((e) => e.tooltipSpace)) == null ? void 0 : r.tooltipSpace) || xc
	};
} }), Cc = /*@__PURE__*/ new WeakMap(), wc = /*@__PURE__*/ W.fromClass(class {
	constructor(e) {
		this.view = e, this.above = [], this.inView = !0, this.madeAbsolute = !1, this.lastTransaction = 0, this.measureTimeout = -1;
		let t = e.state.facet(Sc);
		this.position = t.position, this.parent = t.parent, this.classes = e.themeClasses, this.createContainer(), this.measureReq = {
			read: this.readMeasure.bind(this),
			write: this.writeMeasure.bind(this),
			key: this
		}, this.resizeObserver = typeof ResizeObserver == "function" ? new ResizeObserver(() => this.measureSoon()) : null, this.manager = new bc(e, Oc, (e, t) => this.createTooltip(e, t), (e) => {
			this.resizeObserver && this.resizeObserver.unobserve(e.dom), e.dom.remove();
		}), this.above = this.manager.tooltips.map((e) => !!e.above), this.intersectionObserver = typeof IntersectionObserver == "function" ? new IntersectionObserver((e) => {
			Date.now() > this.lastTransaction - 50 && e.length > 0 && e[e.length - 1].intersectionRatio < 1 && this.measureSoon();
		}, { threshold: [1] }) : null, this.observeIntersection(), e.win.addEventListener("resize", this.measureSoon = this.measureSoon.bind(this)), this.maybeMeasure();
	}
	createContainer() {
		this.parent ? (this.container = document.createElement("div"), this.container.style.position = "relative", this.container.className = this.view.themeClasses, this.parent.appendChild(this.container)) : this.container = this.view.dom;
	}
	observeIntersection() {
		if (this.intersectionObserver) {
			this.intersectionObserver.disconnect();
			for (let e of this.manager.tooltipViews) this.intersectionObserver.observe(e.dom);
		}
	}
	measureSoon() {
		this.measureTimeout < 0 && (this.measureTimeout = setTimeout(() => {
			this.measureTimeout = -1, this.maybeMeasure();
		}, 50));
	}
	update(e) {
		e.transactions.length && (this.lastTransaction = Date.now());
		let t = this.manager.update(e, this.above);
		t && this.observeIntersection();
		let n = t || e.geometryChanged, r = e.state.facet(Sc);
		if (r.position != this.position && !this.madeAbsolute) {
			this.position = r.position;
			for (let e of this.manager.tooltipViews) e.dom.style.position = this.position;
			n = !0;
		}
		if (r.parent != this.parent) {
			this.parent && this.container.remove(), this.parent = r.parent, this.createContainer();
			for (let e of this.manager.tooltipViews) this.container.appendChild(e.dom);
			n = !0;
		} else this.parent && this.view.themeClasses != this.classes && (this.classes = this.container.className = this.view.themeClasses);
		n && this.maybeMeasure();
	}
	createTooltip(e, t) {
		let n = e.create(this.view), r = t ? t.dom : null;
		if (n.dom.classList.add("cm-tooltip"), e.arrow && !n.dom.querySelector(".cm-tooltip > .cm-tooltip-arrow")) {
			let e = document.createElement("div");
			e.className = "cm-tooltip-arrow", n.dom.appendChild(e);
		}
		return n.dom.style.position = this.position, n.dom.style.top = yc, n.dom.style.left = "0px", this.container.insertBefore(n.dom, r), n.mount && n.mount(this.view), this.resizeObserver && this.resizeObserver.observe(n.dom), n;
	}
	destroy() {
		var e, t, n;
		this.view.win.removeEventListener("resize", this.measureSoon);
		for (let t of this.manager.tooltipViews) t.dom.remove(), (e = t.destroy) == null || e.call(t);
		this.parent && this.container.remove(), (t = this.resizeObserver) == null || t.disconnect(), (n = this.intersectionObserver) == null || n.disconnect(), clearTimeout(this.measureTimeout);
	}
	readMeasure() {
		let e = 1, t = 1, n = !1;
		if (this.position == "fixed" && this.manager.tooltipViews.length) {
			let { dom: e } = this.manager.tooltipViews[0];
			if (R.safari) {
				let t = e.getBoundingClientRect();
				n = Math.abs(t.top + 1e4) > 1 || Math.abs(t.left) > 1;
			} else n = !!e.offsetParent && e.offsetParent != this.container.ownerDocument.body;
		}
		if (n || this.position == "absolute") {
			if (this.parent) {
				let n = this.parent.getBoundingClientRect();
				n.width && n.height && (e = n.width / this.parent.offsetWidth, t = n.height / this.parent.offsetHeight);
			} else ({scaleX: e, scaleY: t} = this.view.viewState);
		}
		let r = this.view.scrollDOM.getBoundingClientRect(), i = fi(this.view);
		return {
			visible: {
				left: r.left + i.left,
				top: r.top + i.top,
				right: r.right - i.right,
				bottom: r.bottom - i.bottom
			},
			parent: this.parent ? this.container.getBoundingClientRect() : this.view.dom.getBoundingClientRect(),
			pos: this.manager.tooltips.map((e, t) => {
				let n = this.manager.tooltipViews[t];
				return n.getCoords ? n.getCoords(e.pos) : this.view.coordsAtPos(e.pos);
			}),
			size: this.manager.tooltipViews.map(({ dom: e }) => e.getBoundingClientRect()),
			space: this.view.state.facet(Sc).tooltipSpace(this.view),
			scaleX: e,
			scaleY: t,
			makeAbsolute: n
		};
	}
	writeMeasure(e) {
		var t;
		if (e.makeAbsolute) {
			this.madeAbsolute = !0, this.position = "absolute";
			for (let e of this.manager.tooltipViews) e.dom.style.position = "absolute";
		}
		let { visible: n, space: r, scaleX: i, scaleY: a } = e, o = [];
		for (let s = 0; s < this.manager.tooltips.length; s++) {
			let c = this.manager.tooltips[s], l = this.manager.tooltipViews[s], { dom: u } = l, d = e.pos[s], f = e.size[s];
			if (!d || c.clip !== !1 && (d.bottom <= Math.max(n.top, r.top) || d.top >= Math.min(n.bottom, r.bottom) || d.right < Math.max(n.left, r.left) - .1 || d.left > Math.min(n.right, r.right) + .1)) {
				u.style.top = yc;
				continue;
			}
			let p = c.arrow ? l.dom.querySelector(".cm-tooltip-arrow") : null, m = p ? 7 : 0, h = f.right - f.left, g = (t = Cc.get(l)) == null ? f.bottom - f.top : t, _ = l.offset || Dc, v = this.view.textDirection == V.LTR, y = f.width > r.right - r.left ? v ? r.left : r.right - f.width : v ? Math.max(r.left, Math.min(d.left - (p ? 14 : 0) + _.x, r.right - h)) : Math.min(Math.max(r.left, d.left - h + (p ? 14 : 0) - _.x), r.right - h), b = this.above[s];
			!c.strictSide && (b ? d.top - g - m - _.y < r.top : d.bottom + g + m + _.y > r.bottom) && b == r.bottom - d.bottom > d.top - r.top && (b = this.above[s] = !b);
			let ee = (b ? d.top - r.top : r.bottom - d.bottom) - m;
			if (ee < g && l.resize !== !1) {
				if (ee < this.view.defaultLineHeight) {
					u.style.top = yc;
					continue;
				}
				Cc.set(l, g), u.style.height = (g = ee) / a + "px";
			} else u.style.height && (u.style.height = "");
			let x = b ? d.top - g - m - _.y : d.bottom + m + _.y, S = y + h;
			if (l.overlap !== !0) for (let e of o) e.left < S && e.right > y && e.top < x + g && e.bottom > x && (x = b ? e.top - g - 2 - m : e.bottom + m + 2);
			if (this.position == "absolute" ? (u.style.top = (x - e.parent.top) / a + "px", Tc(u, (y - e.parent.left) / i)) : (u.style.top = x / a + "px", Tc(u, y / i)), p) {
				let e = d.left + (v ? _.x : -_.x) - (y + 14 - 7);
				p.style.left = e / i + "px";
			}
			l.overlap !== !0 && o.push({
				left: y,
				top: x,
				right: S,
				bottom: x + g
			}), u.classList.toggle("cm-tooltip-above", b), u.classList.toggle("cm-tooltip-below", !b), l.positioned && l.positioned(e.space);
		}
	}
	maybeMeasure() {
		if (this.manager.tooltips.length && (this.view.inView && this.view.requestMeasure(this.measureReq), this.inView != this.view.inView && (this.inView = this.view.inView, !this.inView))) for (let e of this.manager.tooltipViews) e.dom.style.top = yc;
	}
}, { eventObservers: { scroll() {
	this.maybeMeasure();
} } });
function Tc(e, t) {
	let n = parseInt(e.style.left, 10);
	(isNaN(n) || Math.abs(t - n) > 1) && (e.style.left = t + "px");
}
var Ec = /*@__PURE__*/ J.baseTheme({
	".cm-tooltip": {
		zIndex: 500,
		boxSizing: "border-box"
	},
	"&light .cm-tooltip": {
		border: "1px solid #bbb",
		backgroundColor: "#f5f5f5"
	},
	"&light .cm-tooltip-section:not(:first-child)": { borderTop: "1px solid #bbb" },
	"&dark .cm-tooltip": {
		backgroundColor: "#333338",
		color: "white"
	},
	".cm-tooltip-arrow": {
		height: "7px",
		width: "14px",
		position: "absolute",
		zIndex: -1,
		overflow: "hidden",
		"&:before, &:after": {
			content: "''",
			position: "absolute",
			width: 0,
			height: 0,
			borderLeft: "7px solid transparent",
			borderRight: "7px solid transparent"
		},
		".cm-tooltip-above &": {
			bottom: "-7px",
			"&:before": { borderTop: "7px solid #bbb" },
			"&:after": {
				borderTop: "7px solid #f5f5f5",
				bottom: "1px"
			}
		},
		".cm-tooltip-below &": {
			top: "-7px",
			"&:before": { borderBottom: "7px solid #bbb" },
			"&:after": {
				borderBottom: "7px solid #f5f5f5",
				top: "1px"
			}
		}
	},
	"&dark .cm-tooltip .cm-tooltip-arrow": {
		"&:before": {
			borderTopColor: "#333338",
			borderBottomColor: "#333338"
		},
		"&:after": {
			borderTopColor: "transparent",
			borderBottomColor: "transparent"
		}
	}
}), Dc = {
	x: 0,
	y: 0
}, Oc = /*@__PURE__*/ O.define({ enables: [wc, Ec] }), kc = /*@__PURE__*/ O.define({ combine: (e) => e.reduce((e, t) => e.concat(t), []) }), Ac = class e {
	static create(t) {
		return new e(t);
	}
	constructor(e) {
		this.view = e, this.mounted = !1, this.dom = document.createElement("div"), this.dom.classList.add("cm-tooltip-hover"), this.manager = new bc(e, kc, (e, t) => this.createHostedView(e, t), (e) => e.dom.remove());
	}
	createHostedView(e, t) {
		let n = e.create(this.view);
		return n.dom.classList.add("cm-tooltip-section"), this.dom.insertBefore(n.dom, t ? t.dom.nextSibling : this.dom.firstChild), this.mounted && n.mount && n.mount(this.view), n;
	}
	mount(e) {
		for (let t of this.manager.tooltipViews) t.mount && t.mount(e);
		this.mounted = !0;
	}
	positioned(e) {
		for (let t of this.manager.tooltipViews) t.positioned && t.positioned(e);
	}
	update(e) {
		this.manager.update(e);
	}
	destroy() {
		var e;
		for (let t of this.manager.tooltipViews) (e = t.destroy) == null || e.call(t);
	}
	passProp(e) {
		let t;
		for (let n of this.manager.tooltipViews) {
			let r = n[e];
			if (r !== void 0) {
				if (t === void 0) t = r;
				else if (t !== r) return;
			}
		}
		return t;
	}
	get offset() {
		return this.passProp("offset");
	}
	get getCoords() {
		return this.passProp("getCoords");
	}
	get overlap() {
		return this.passProp("overlap");
	}
	get resize() {
		return this.passProp("resize");
	}
}, jc = /*@__PURE__*/ Oc.compute([kc], (e) => {
	let t = e.facet(kc);
	return t.length === 0 ? null : {
		pos: Math.min(...t.map((e) => e.pos)),
		end: Math.max(...t.map((e) => {
			var t;
			return (t = e.end) == null ? e.pos : t;
		})),
		create: Ac.create,
		above: t[0].above,
		arrow: t.some((e) => e.arrow)
	};
}), Mc = /*@__PURE__*/ O.define(), Nc = class {
	constructor(e, t, n, r, i, a) {
		this.view = e, this.source = t, this.field = n, this.locked = r, this.setHover = i, this.hoverTime = a, this.hoverTimeout = -1, this.restartTimeout = -1, this.pending = null, this.lastMove = {
			x: 0,
			y: 0,
			target: e.dom,
			time: 0
		}, this.checkHover = this.checkHover.bind(this), e.dom.addEventListener("mouseleave", this.mouseleave = this.mouseleave.bind(this)), e.dom.addEventListener("mousemove", this.mousemove = this.mousemove.bind(this));
	}
	update(e) {
		this.pending && (this.pending = null, clearTimeout(this.restartTimeout), this.restartTimeout = setTimeout(() => this.startHover(), 20));
	}
	get active() {
		return this.view.state.field(this.field);
	}
	checkHover() {
		if (this.hoverTimeout = -1, this.active.length) return;
		let e = Date.now() - this.lastMove.time;
		e < this.hoverTime ? this.hoverTimeout = setTimeout(this.checkHover, this.hoverTime - e) : this.startHover();
	}
	startHover() {
		clearTimeout(this.restartTimeout);
		let { view: e, lastMove: t } = this, n = e.docView.tile.nearest(t.target);
		if (!n) return;
		let r, i = 1;
		if (n.isWidget()) r = n.posAtStart;
		else {
			if (r = e.posAtCoords(t), r == null) return;
			let n = e.coordsAtPos(r);
			if (!n || t.y < n.top || t.y > n.bottom || t.x < n.left - e.defaultCharacterWidth || t.x > n.right + e.defaultCharacterWidth) return;
			let a = e.bidiSpans(e.state.doc.lineAt(r)).find((e) => e.from <= r && e.to >= r), o = a && a.dir == V.RTL ? -1 : 1;
			i = t.x < n.left ? -o : o;
		}
		this.activateHover(e, r, i);
	}
	activateHover(e, t, n, r) {
		let i = this.source(e, t, n), a = (t) => {
			if (t && !(Array.isArray(t) && !t.length)) {
				let n = Array.isArray(t) ? t : [t];
				r && this.locked.set(n, r), e.dispatch({ effects: this.setHover.of(n) });
			}
		};
		if (i && "then" in i) {
			let n = this.pending = { pos: t };
			i.then((e) => {
				this.pending == n && (this.pending = null, a(e));
			}, (t) => U(e.state, t, "hover tooltip"));
		} else a(i);
	}
	get tooltip() {
		let e = this.view.plugin(wc), t = e ? e.manager.tooltips.findIndex((e) => e.create == Ac.create) : -1;
		return t > -1 ? e.manager.tooltipViews[t] : null;
	}
	mousemove(e) {
		var t, n;
		this.lastMove = {
			x: e.clientX,
			y: e.clientY,
			target: e.target,
			time: Date.now()
		}, this.hoverTimeout < 0 && (this.hoverTimeout = setTimeout(this.checkHover, this.hoverTime));
		let { active: r, tooltip: i } = this;
		if (r.length && !this.locked.has(r) && i && !Fc(i.dom, e) || this.pending) {
			let { pos: i } = r[0] || this.pending, a = (n = (t = r[0]) == null ? void 0 : t.end) == null ? i : n;
			(i == a ? this.view.posAtCoords(this.lastMove) != i : !Ic(this.view, i, a, e.clientX, e.clientY)) && (this.view.dispatch({ effects: this.setHover.of([]) }), this.pending = null);
		}
	}
	mouseleave(e) {
		clearTimeout(this.hoverTimeout), this.hoverTimeout = -1;
		let { active: t } = this;
		if (t.length && !this.locked.has(t)) {
			let { tooltip: t } = this;
			t && t.dom.contains(e.relatedTarget) ? this.watchTooltipLeave(t.dom) : this.view.dispatch({ effects: this.setHover.of([]) });
		}
	}
	watchTooltipLeave(e) {
		let t = (n) => {
			e.removeEventListener("mouseleave", t);
			let { active: r } = this;
			r.length && !this.locked.has(r) && !this.view.dom.contains(n.relatedTarget) && this.view.dispatch({ effects: this.setHover.of([]) });
		};
		e.addEventListener("mouseleave", t);
	}
	destroy() {
		clearTimeout(this.hoverTimeout), clearTimeout(this.restartTimeout), this.view.dom.removeEventListener("mouseleave", this.mouseleave), this.view.dom.removeEventListener("mousemove", this.mousemove);
	}
}, Pc = 4;
function Fc(e, t) {
	let { left: n, right: r, top: i, bottom: a } = e.getBoundingClientRect(), o;
	if (o = e.querySelector(".cm-tooltip-arrow")) {
		let e = o.getBoundingClientRect();
		i = Math.min(e.top, i), a = Math.max(e.bottom, a);
	}
	return t.clientX >= n - Pc && t.clientX <= r + Pc && t.clientY >= i - Pc && t.clientY <= a + Pc;
}
function Ic(e, t, n, r, i, a) {
	let o = e.scrollDOM.getBoundingClientRect(), s = e.documentTop + e.documentPadding.top + e.contentHeight;
	if (o.left > r || o.right < r || o.top > i || Math.min(o.bottom, s) < i) return !1;
	let c = e.posAtCoords({
		x: r,
		y: i
	}, !1);
	return c >= t && c <= n;
}
function Lc(e, t = {}) {
	let n = A.define(), r = /* @__PURE__ */ new WeakMap(), i = k.define({
		create() {
			return [];
		},
		update(e, a) {
			let o = r.get(e);
			if (e.length && (t.hideOnChange && (a.docChanged || a.selection) || o && o(a) ? e = [] : t.hideOn && (e = e.filter((e) => !t.hideOn(a, e)))), a.docChanged && e.length) {
				let t = [];
				for (let n of e) {
					let e = a.changes.mapPos(n.pos, -1, T.TrackDel);
					if (e != null) {
						let r = Object.assign(Object.create(null), n);
						r.pos = e, r.end != null && (r.end = a.changes.mapPos(r.end)), t.push(r);
					}
				}
				e = t;
			}
			for (let t of a.effects) t.is(n) && (e = t.value, o = void 0), (t.is(Bc) && !t.value || t.value == i) && (e = []);
			return e.length && o && r.set(e, o), e;
		},
		provide: (e) => kc.from(e)
	}), a = W.define((a) => new Nc(a, e, i, r, n, t.hoverTime || 300));
	return {
		active: i,
		extension: [
			i,
			a,
			Mc.of(a),
			jc
		]
	};
}
function Rc(e, t, n, r = {}) {
	var i;
	let a = e.state.facet(Mc).map((t) => e.plugin(t)).filter((e) => !!e);
	if (r.tooltip && r.tooltip.active) {
		let e = a.find((e) => e.field == r.tooltip.active);
		e && (a = [e]);
	}
	for (let o of a) o.activateHover(e, t, n, (i = r.until) == null ? (() => !1) : i);
}
function zc(e, t) {
	let n = e.plugin(wc);
	if (!n) return null;
	let r = n.manager.tooltips.indexOf(t);
	return r < 0 ? null : n.manager.tooltipViews[r];
}
var Bc = /*@__PURE__*/ A.define(), Vc = /*@__PURE__*/ O.define({ combine(e) {
	let t, n;
	for (let r of e) t = t || r.topContainer, n = n || r.bottomContainer;
	return {
		topContainer: t,
		bottomContainer: n
	};
} });
function Hc(e, t) {
	let n = e.plugin(Uc), r = n ? n.specs.indexOf(t) : -1;
	return r > -1 ? n.panels[r] : null;
}
var Uc = /*@__PURE__*/ W.fromClass(class {
	constructor(e) {
		this.input = e.state.facet(Kc), this.specs = this.input.filter((e) => e), this.panels = this.specs.map((t) => t(e));
		let t = e.state.facet(Vc);
		this.top = new Wc(e, !0, t.topContainer), this.bottom = new Wc(e, !1, t.bottomContainer), this.top.sync(this.panels.filter((e) => e.top)), this.bottom.sync(this.panels.filter((e) => !e.top));
		for (let e of this.panels) e.dom.classList.add("cm-panel"), e.mount && e.mount();
	}
	update(e) {
		let t = e.state.facet(Vc);
		this.top.container != t.topContainer && (this.top.sync([]), this.top = new Wc(e.view, !0, t.topContainer)), this.bottom.container != t.bottomContainer && (this.bottom.sync([]), this.bottom = new Wc(e.view, !1, t.bottomContainer)), this.top.syncClasses(), this.bottom.syncClasses();
		let n = e.state.facet(Kc);
		if (n != this.input) {
			let t = n.filter((e) => e), r = [], i = [], a = [], o = [];
			for (let n of t) {
				let t = this.specs.indexOf(n), s;
				t < 0 ? (s = n(e.view), o.push(s)) : (s = this.panels[t], s.update && s.update(e)), r.push(s), (s.top ? i : a).push(s);
			}
			this.specs = t, this.panels = r, this.top.sync(i), this.bottom.sync(a);
			for (let e of o) e.dom.classList.add("cm-panel"), e.mount && e.mount();
		} else for (let t of this.panels) t.update && t.update(e);
	}
	destroy() {
		this.top.sync([]), this.bottom.sync([]);
	}
}, { provide: (e) => J.scrollMargins.of((t) => {
	let n = t.plugin(e);
	return n && {
		top: n.top.scrollMargin(),
		bottom: n.bottom.scrollMargin()
	};
}) }), Wc = class {
	constructor(e, t, n) {
		this.view = e, this.top = t, this.container = n, this.dom = void 0, this.classes = "", this.panels = [], this.syncClasses();
	}
	sync(e) {
		for (let t of this.panels) t.destroy && e.indexOf(t) < 0 && t.destroy();
		this.panels = e, this.syncDOM();
	}
	syncDOM() {
		if (this.panels.length == 0) {
			this.dom && (this.dom.remove(), this.dom = void 0);
			return;
		}
		if (!this.dom) {
			this.dom = document.createElement("div"), this.dom.className = this.top ? "cm-panels cm-panels-top" : "cm-panels cm-panels-bottom";
			let e = this.container || this.view.dom;
			e.insertBefore(this.dom, this.top ? e.firstChild : null);
		}
		let e = this.dom.firstChild;
		for (let t of this.panels) if (t.dom.parentNode == this.dom) {
			for (; e != t.dom;) e = Gc(e);
			e = e.nextSibling;
		} else this.dom.insertBefore(t.dom, e);
		for (; e;) e = Gc(e);
	}
	scrollMargin() {
		return !this.dom || this.container ? 0 : Math.max(0, this.top ? this.dom.getBoundingClientRect().bottom - Math.max(0, this.view.scrollDOM.getBoundingClientRect().top) : Math.min(innerHeight, this.view.scrollDOM.getBoundingClientRect().bottom) - this.dom.getBoundingClientRect().top);
	}
	syncClasses() {
		if (!(!this.container || this.classes == this.view.themeClasses)) {
			for (let e of this.classes.split(" ")) e && this.container.classList.remove(e);
			for (let e of (this.classes = this.view.themeClasses).split(" ")) e && this.container.classList.add(e);
		}
	}
};
function Gc(e) {
	let t = e.nextSibling;
	return e.remove(), t;
}
var Kc = /*@__PURE__*/ O.define({ enables: Uc });
function qc(e, t) {
	let n, r = new Promise((e) => n = e), i = (e) => Zc(e, t, n);
	e.state.field(Jc, !1) ? e.dispatch({ effects: Yc.of(i) }) : e.dispatch({ effects: A.appendConfig.of(Jc.init(() => [i])) });
	let a = Xc.of(i);
	return {
		close: a,
		result: r.then((t) => ((e.win.queueMicrotask || ((t) => e.win.setTimeout(t, 10)))(() => {
			e.state.field(Jc).indexOf(i) > -1 && e.dispatch({ effects: a });
		}), t))
	};
}
var Jc = /*@__PURE__*/ k.define({
	create() {
		return [];
	},
	update(e, t) {
		for (let n of t.effects) n.is(Yc) ? e = [n.value].concat(e) : n.is(Xc) && (e = e.filter((e) => e != n.value));
		return e;
	},
	provide: (e) => Kc.computeN([e], (t) => t.field(e))
}), Yc = /*@__PURE__*/ A.define(), Xc = /*@__PURE__*/ A.define();
function Zc(e, t, n) {
	let r = t.content ? t.content(e, () => o(null)) : null;
	if (!r) {
		if (r = I("form"), t.input) {
			let e = I("input", t.input);
			/^(text|password|number|email|tel|url)$/.test(e.type) && e.classList.add("cm-textfield"), e.name || (e.name = "input"), r.appendChild(I("label", (t.label || "") + ": ", e));
		} else r.appendChild(document.createTextNode(t.label || ""));
		r.appendChild(document.createTextNode(" ")), r.appendChild(I("button", {
			class: "cm-button",
			type: "submit"
		}, t.submitLabel || "OK"));
	}
	let i = r.nodeName == "FORM" ? [r] : r.querySelectorAll("form");
	for (let e = 0; e < i.length; e++) {
		let t = i[e];
		t.addEventListener("keydown", (e) => {
			e.keyCode == 27 ? (e.preventDefault(), o(null)) : e.keyCode == 13 && (e.preventDefault(), o(t));
		}), t.addEventListener("submit", (e) => {
			e.preventDefault(), o(t);
		});
	}
	let a = I("div", r, I("button", {
		onclick: () => o(null),
		"aria-label": e.state.phrase("close"),
		class: "cm-dialog-close",
		type: "button"
	}, ["×"]));
	t.class && (a.className = t.class), a.classList.add("cm-dialog");
	function o(t) {
		a.contains(a.ownerDocument.activeElement) && e.focus(), n(t);
	}
	return {
		dom: a,
		top: t.top,
		mount: () => {
			if (t.focus) {
				let e;
				e = typeof t.focus == "string" ? r.querySelector(t.focus) : r.querySelector("input") || r.querySelector("button"), e && "select" in e ? e.select() : e && "focus" in e && e.focus();
			}
		}
	};
}
var Qc = class extends Nt {
	compare(e) {
		return this == e || this.constructor == e.constructor && this.eq(e);
	}
	eq(e) {
		return !1;
	}
	destroy(e) {}
};
Qc.prototype.elementClass = "", Qc.prototype.toDOM = void 0, Qc.prototype.mapMode = T.TrackBefore, Qc.prototype.startSide = Qc.prototype.endSide = -1, Qc.prototype.point = !0;
var $c = /*@__PURE__*/ O.define(), el = /*@__PURE__*/ O.define(), tl = {
	class: "",
	renderEmptyElements: !1,
	elementStyle: "",
	markers: () => P.empty,
	lineMarker: () => null,
	widgetMarker: () => null,
	lineMarkerChange: null,
	initialSpacer: null,
	updateSpacer: null,
	domEventHandlers: {},
	side: "before"
}, nl = /*@__PURE__*/ O.define();
function rl(e) {
	return [al(), nl.of(vn(vn({}, tl), e))];
}
var il = /*@__PURE__*/ O.define({ combine: (e) => e.some((e) => e) });
function al(e) {
	let t = [ol];
	return e && e.fixed === !1 && t.push(il.of(!0)), t;
}
var ol = /*@__PURE__*/ W.fromClass(class {
	constructor(e) {
		this.view = e, this.domAfter = null, this.prevViewport = e.viewport, this.dom = document.createElement("div"), this.dom.className = "cm-gutters cm-gutters-before", this.dom.setAttribute("aria-hidden", "true"), this.dom.style.minHeight = this.view.contentHeight / this.view.scaleY + "px", this.gutters = e.state.facet(nl).map((t) => new ul(e, t)), this.fixed = !e.state.facet(il);
		for (let e of this.gutters) e.config.side == "after" ? this.getDOMAfter().appendChild(e.dom) : this.dom.appendChild(e.dom);
		this.fixed && (this.dom.style.position = "sticky"), this.syncGutters(!1), e.scrollDOM.insertBefore(this.dom, e.contentDOM);
	}
	getDOMAfter() {
		return this.domAfter || (this.domAfter = document.createElement("div"), this.domAfter.className = "cm-gutters cm-gutters-after", this.domAfter.setAttribute("aria-hidden", "true"), this.domAfter.style.minHeight = this.view.contentHeight / this.view.scaleY + "px", this.domAfter.style.position = this.fixed ? "sticky" : "", this.view.scrollDOM.appendChild(this.domAfter)), this.domAfter;
	}
	update(e) {
		if (this.updateGutters(e)) {
			let t = this.prevViewport, n = e.view.viewport, r = Math.min(t.to, n.to) - Math.max(t.from, n.from);
			this.syncGutters(r < (n.to - n.from) * .8);
		}
		if (e.geometryChanged) {
			let e = this.view.contentHeight / this.view.scaleY + "px";
			this.dom.style.minHeight = e, this.domAfter && (this.domAfter.style.minHeight = e);
		}
		this.view.state.facet(il) != !this.fixed && (this.fixed = !this.fixed, this.dom.style.position = this.fixed ? "sticky" : "", this.domAfter && (this.domAfter.style.position = this.fixed ? "sticky" : "")), this.prevViewport = e.view.viewport;
	}
	syncGutters(e) {
		let t = this.dom.nextSibling;
		e && (this.dom.remove(), this.domAfter && this.domAfter.remove());
		let n = P.iter(this.view.state.facet($c), this.view.viewport.from), r = [], i = this.gutters.map((e) => new ll(e, this.view.viewport, -this.view.documentPadding.top));
		for (let e of this.view.viewportLineBlocks) if (r.length && (r = []), Array.isArray(e.type)) {
			let t = !0;
			for (let a of e.type) if (a.type == z.Text && t) {
				cl(n, r, a.from);
				for (let e of i) e.line(this.view, a, r);
				t = !1;
			} else if (a.widget) for (let e of i) e.widget(this.view, a);
		} else if (e.type == z.Text) {
			cl(n, r, e.from);
			for (let t of i) t.line(this.view, e, r);
		} else if (e.widget) for (let t of i) t.widget(this.view, e);
		for (let e of i) e.finish();
		e && (this.view.scrollDOM.insertBefore(this.dom, t), this.domAfter && this.view.scrollDOM.appendChild(this.domAfter));
	}
	updateGutters(e) {
		let t = e.startState.facet(nl), n = e.state.facet(nl), r = e.docChanged || e.heightChanged || e.viewportChanged || !P.eq(e.startState.facet($c), e.state.facet($c), e.view.viewport.from, e.view.viewport.to);
		if (t == n) for (let t of this.gutters) t.update(e) && (r = !0);
		else {
			r = !0;
			let i = [];
			for (let r of n) {
				let n = t.indexOf(r);
				n < 0 ? i.push(new ul(this.view, r)) : (this.gutters[n].update(e), i.push(this.gutters[n]));
			}
			for (let e of this.gutters) e.dom.remove(), i.indexOf(e) < 0 && e.destroy();
			for (let e of i) e.config.side == "after" ? this.getDOMAfter().appendChild(e.dom) : this.dom.appendChild(e.dom);
			this.gutters = i;
		}
		return r;
	}
	destroy() {
		for (let e of this.gutters) e.destroy();
		this.dom.remove(), this.domAfter && this.domAfter.remove();
	}
}, { provide: (e) => J.scrollMargins.of((t) => {
	let n = t.plugin(e);
	if (!n || n.gutters.length == 0 || !n.fixed) return null;
	let r = n.dom.offsetWidth * t.scaleX, i = n.domAfter ? n.domAfter.offsetWidth * t.scaleX : 0;
	return t.textDirection == V.LTR ? {
		left: r,
		right: i
	} : {
		right: r,
		left: i
	};
}) });
function sl(e) {
	return Array.isArray(e) ? e : [e];
}
function cl(e, t, n) {
	for (; e.value && e.from <= n;) e.from == n && t.push(e.value), e.next();
}
var ll = class {
	constructor(e, t, n) {
		this.gutter = e, this.height = n, this.i = 0, this.cursor = P.iter(e.markers, t.from);
	}
	addElement(e, t, n) {
		let { gutter: r } = this, i = (t.top - this.height) / e.scaleY, a = t.height / e.scaleY;
		if (this.i == r.elements.length) {
			let t = new dl(e, a, i, n);
			r.elements.push(t), r.dom.appendChild(t.dom);
		} else r.elements[this.i].update(e, a, i, n);
		this.height = t.bottom, this.i++;
	}
	line(e, t, n) {
		let r = [];
		cl(this.cursor, r, t.from), n.length && (r = r.concat(n));
		let i = this.gutter.config.lineMarker(e, t, r);
		i && r.unshift(i);
		let a = this.gutter;
		r.length == 0 && !a.config.renderEmptyElements || this.addElement(e, t, r);
	}
	widget(e, t) {
		let n = this.gutter.config.widgetMarker(e, t.widget, t), r = n ? [n] : null;
		for (let n of e.state.facet(el)) {
			let i = n(e, t.widget, t);
			i && (r || (r = [])).push(i);
		}
		r && this.addElement(e, t, r);
	}
	finish() {
		let e = this.gutter;
		for (; e.elements.length > this.i;) {
			let t = e.elements.pop();
			e.dom.removeChild(t.dom), t.destroy();
		}
	}
}, ul = class {
	constructor(e, t) {
		this.view = e, this.config = t, this.elements = [], this.spacer = null, this.dom = document.createElement("div"), this.dom.className = "cm-gutter" + (this.config.class ? " " + this.config.class : "");
		for (let n in t.domEventHandlers) this.dom.addEventListener(n, (r) => {
			let i = r.target, a;
			if (i != this.dom && this.dom.contains(i)) {
				for (; i.parentNode != this.dom;) i = i.parentNode;
				let e = i.getBoundingClientRect();
				a = (e.top + e.bottom) / 2;
			} else a = r.clientY;
			let o = e.lineBlockAtHeight(a - e.documentTop);
			t.domEventHandlers[n](e, o, r) && r.preventDefault();
		});
		this.markers = sl(t.markers(e)), t.initialSpacer && (this.spacer = new dl(e, 0, 0, [t.initialSpacer(e)]), this.dom.appendChild(this.spacer.dom), this.spacer.dom.style.cssText += "visibility: hidden; pointer-events: none");
	}
	update(e) {
		let t = this.markers;
		if (this.markers = sl(this.config.markers(e.view)), this.spacer && this.config.updateSpacer) {
			let t = this.config.updateSpacer(this.spacer.markers[0], e);
			t != this.spacer.markers[0] && this.spacer.update(e.view, 0, 0, [t]);
		}
		let n = e.view.viewport;
		return !P.eq(this.markers, t, n.from, n.to) || (this.config.lineMarkerChange ? this.config.lineMarkerChange(e) : !1);
	}
	destroy() {
		for (let e of this.elements) e.destroy();
	}
}, dl = class {
	constructor(e, t, n, r) {
		this.height = -1, this.above = 0, this.markers = [], this.dom = document.createElement("div"), this.dom.className = "cm-gutterElement", this.update(e, t, n, r);
	}
	update(e, t, n, r) {
		this.height != t && (this.height = t, this.dom.style.height = t + "px"), this.above != n && (this.dom.style.marginTop = (this.above = n) ? n + "px" : ""), fl(this.markers, r) || this.setMarkers(e, r);
	}
	setMarkers(e, t) {
		let n = "cm-gutterElement", r = this.dom.firstChild;
		for (let i = 0, a = 0;;) {
			let o = a, s = i < t.length ? t[i++] : null, c = !1;
			if (s) {
				let e = s.elementClass;
				e && (n += " " + e);
				for (let e = a; e < this.markers.length; e++) if (this.markers[e].compare(s)) {
					o = e, c = !0;
					break;
				}
			} else o = this.markers.length;
			for (; a < o;) {
				let e = this.markers[a++];
				if (e.toDOM) {
					e.destroy(r);
					let t = r.nextSibling;
					r.remove(), r = t;
				}
			}
			if (!s) break;
			s.toDOM && (c ? r = r.nextSibling : this.dom.insertBefore(s.toDOM(e), r)), c && a++;
		}
		this.dom.className = n, this.markers = t;
	}
	destroy() {
		this.setMarkers(null, []);
	}
};
function fl(e, t) {
	if (e.length != t.length) return !1;
	for (let n = 0; n < e.length; n++) if (!e[n].compare(t[n])) return !1;
	return !0;
}
var pl = /*@__PURE__*/ O.define(), ml = /*@__PURE__*/ O.define(), hl = /*@__PURE__*/ O.define({ combine(e) {
	return Mt(e, {
		formatNumber: String,
		domEventHandlers: {}
	}, { domEventHandlers(e, t) {
		let n = Object.assign({}, e);
		for (let e in t) {
			let r = n[e], i = t[e];
			n[e] = r ? (e, t, n) => r(e, t, n) || i(e, t, n) : i;
		}
		return n;
	} });
} }), gl = class extends Qc {
	constructor(e) {
		super(), this.number = e;
	}
	eq(e) {
		return this.number == e.number;
	}
	toDOM() {
		return document.createTextNode(this.number);
	}
};
function _l(e, t) {
	return e.state.facet(hl).formatNumber(t, e.state);
}
var vl = /*@__PURE__*/ nl.compute([hl], (e) => ({
	class: "cm-lineNumbers",
	renderEmptyElements: !1,
	markers(e) {
		return e.state.facet(pl);
	},
	lineMarker(e, t, n) {
		return n.some((e) => e.toDOM) ? null : new gl(_l(e, e.state.doc.lineAt(t.from).number));
	},
	widgetMarker: (e, t, n) => {
		for (let r of e.state.facet(ml)) {
			let i = r(e, t, n);
			if (i) return i;
		}
		return null;
	},
	lineMarkerChange: (e) => e.startState.facet(hl) != e.state.facet(hl),
	initialSpacer(e) {
		return new gl(_l(e, bl(e.state.doc.lines)));
	},
	updateSpacer(e, t) {
		let n = _l(t.view, bl(t.view.state.doc.lines));
		return n == e.number ? e : new gl(n);
	},
	domEventHandlers: e.facet(hl).domEventHandlers,
	side: "before"
}));
function yl(e = {}) {
	return [
		hl.of(e),
		al(),
		vl
	];
}
function bl(e) {
	let t = 9;
	for (; t < e;) t = t * 10 + 9;
	return t;
}
var xl = /*@__PURE__*/ new class extends Qc {
	constructor() {
		super(...arguments), this.elementClass = "cm-activeLineGutter";
	}
}(), Sl = /*@__PURE__*/ $c.compute(["selection"], (e) => {
	let t = [], n = -1;
	for (let r of e.selection.ranges) {
		let i = e.doc.lineAt(r.head).from;
		i > n && (n = i, t.push(xl.range(i)));
	}
	return P.of(t);
});
function Cl() {
	return Sl;
}
//#endregion
//#region node_modules/@lezer/highlight/dist/index.js
var wl = 0, Tl = class e {
	constructor(e, t, n, r) {
		this.name = e, this.set = t, this.base = n, this.modified = r, this.id = wl++;
	}
	toString() {
		let { name: e } = this;
		for (let t of this.modified) t.name && (e = `${t.name}(${e})`);
		return e;
	}
	static define(t, n) {
		let r = typeof t == "string" ? t : "?";
		if (t instanceof e && (n = t), n != null && n.base) throw Error("Can not derive from a modified tag");
		let i = new e(r, [], null, []);
		if (i.set.push(i), n) for (let e of n.set) i.set.push(e);
		return i;
	}
	static defineModifier(e) {
		let t = new Dl(e);
		return (e) => e.modified.indexOf(t) > -1 ? e : Dl.get(e.base || e, e.modified.concat(t).sort((e, t) => e.id - t.id));
	}
}, El = 0, Dl = class e {
	constructor(e) {
		this.name = e, this.instances = [], this.id = El++;
	}
	static get(t, n) {
		if (!n.length) return t;
		let r = n[0].instances.find((e) => e.base == t && Ol(n, e.modified));
		if (r) return r;
		let i = [], a = new Tl(t.name, i, t, n);
		for (let e of n) e.instances.push(a);
		let o = kl(n);
		for (let n of t.set) if (!n.modified.length) for (let t of o) i.push(e.get(n, t));
		return a;
	}
};
function Ol(e, t) {
	return e.length == t.length && e.every((e, n) => e == t[n]);
}
function kl(e) {
	let t = [[]];
	for (let n = 0; n < e.length; n++) for (let r = 0, i = t.length; r < i; r++) t.push(t[r].concat(e[n]));
	return t.sort((e, t) => t.length - e.length);
}
function Al(e) {
	let t = Object.create(null);
	for (let n in e) {
		let r = e[n];
		Array.isArray(r) || (r = [r]);
		for (let e of n.split(" ")) if (e) {
			let n = [], i = 2, a = e;
			for (let t = 0;;) {
				if (a == "..." && t > 0 && t + 3 == e.length) {
					i = 1;
					break;
				}
				let r = /^"(?:[^"\\]|\\.)*?"|[^\/!]+/.exec(a);
				if (!r) throw RangeError("Invalid path: " + e);
				if (n.push(r[0] == "*" ? "" : r[0][0] == "\"" ? JSON.parse(r[0]) : r[0]), t += r[0].length, t == e.length) break;
				let o = e[t++];
				if (t == e.length && o == "!") {
					i = 0;
					break;
				}
				if (o != "/") throw RangeError("Invalid path: " + e);
				a = e.slice(t);
			}
			let o = n.length - 1, s = n[o];
			if (!s) throw RangeError("Invalid path: " + e);
			t[s] = new Ml(r, i, o > 0 ? n.slice(0, o) : null).sort(t[s]);
		}
	}
	return jl.add(t);
}
var jl = new n({ combine(e, t) {
	let n, r, i;
	for (; e || t;) {
		if (!e || t && e.depth >= t.depth ? (i = t, t = t.next) : (i = e, e = e.next), n && n.mode == i.mode && !i.context && !n.context) continue;
		let a = new Ml(i.tags, i.mode, i.context);
		n ? n.next = a : r = a, n = a;
	}
	return r;
} }), Ml = class {
	constructor(e, t, n, r) {
		this.tags = e, this.mode = t, this.context = n, this.next = r;
	}
	get opaque() {
		return this.mode == 0;
	}
	get inherit() {
		return this.mode == 1;
	}
	sort(e) {
		return !e || e.depth < this.depth ? (this.next = e, this) : (e.next = this.sort(e.next), e);
	}
	get depth() {
		return this.context ? this.context.length : 0;
	}
};
Ml.empty = new Ml([], 2, null);
function Nl(e, t) {
	let n = Object.create(null);
	for (let t of e) if (!Array.isArray(t.tag)) n[t.tag.id] = t.class;
	else for (let e of t.tag) n[e.id] = t.class;
	let { scope: r, all: i = null } = t || {};
	return {
		style: (e) => {
			let t = i;
			for (let r of e) for (let e of r.set) {
				let r = n[e.id];
				if (r) {
					t = t ? t + " " + r : r;
					break;
				}
			}
			return t;
		},
		scope: r
	};
}
function Pl(e, t) {
	let n = null;
	for (let r of e) {
		let e = r.style(t);
		e && (n = n ? n + " " + e : e);
	}
	return n;
}
function Fl(e, t, n, r = 0, i = e.length) {
	let a = new Il(r, Array.isArray(t) ? t : [t], n);
	a.highlightRange(e.cursor(), r, i, "", a.highlighters), a.flush(i);
}
var Il = class {
	constructor(e, t, n) {
		this.at = e, this.highlighters = t, this.span = n, this.class = "";
	}
	startSpan(e, t) {
		t != this.class && (this.flush(e), e > this.at && (this.at = e), this.class = t);
	}
	flush(e) {
		e > this.at && this.class && this.span(this.at, e, this.class);
	}
	highlightRange(e, t, r, i, a) {
		let { type: o, from: s, to: c } = e;
		if (s >= r || c <= t) return;
		o.isTop && (a = this.highlighters.filter((e) => !e.scope || e.scope(o)));
		let l = i, u = Ll(e) || Ml.empty, d = Pl(a, u.tags);
		if (d && (l && (l += " "), l += d, u.mode == 1 && (i += (i ? " " : "") + d)), this.startSpan(Math.max(t, s), l), u.opaque) return;
		let f = e.tree && e.tree.prop(n.mounted);
		if (f && f.overlay) {
			let n = e.node.enter(f.overlay[0].from + s, 1), o = this.highlighters.filter((e) => !e.scope || e.scope(f.tree.type)), u = e.firstChild();
			for (let d = 0, p = s;; d++) {
				let m = d < f.overlay.length ? f.overlay[d] : null, h = m ? m.from + s : c, g = Math.max(t, p), _ = Math.min(r, h);
				if (g < _ && u) for (; e.from < _ && (this.highlightRange(e, g, _, i, a), this.startSpan(Math.min(_, e.to), l), !(e.to >= h || !e.nextSibling())););
				if (!m || h > r) break;
				p = m.to + s, p > t && (this.highlightRange(n.cursor(), Math.max(t, m.from + s), Math.min(r, p), "", o), this.startSpan(Math.min(r, p), l));
			}
			u && e.parent();
		} else if (e.firstChild()) {
			f && (i = "");
			do
				if (!(e.to <= t)) {
					if (e.from >= r) break;
					this.highlightRange(e, t, r, i, a), this.startSpan(Math.min(r, e.to), l);
				}
			while (e.nextSibling());
			e.parent();
		}
	}
};
function Ll(e) {
	let t = e.type.prop(jl);
	for (; t && t.context && !e.matchContext(t.context);) t = t.next;
	return t || null;
}
var Y = Tl.define, Rl = Y(), zl = Y(), Bl = Y(zl), Vl = Y(zl), Hl = Y(), Ul = Y(Hl), Wl = Y(Hl), Gl = Y(), Kl = Y(Gl), ql = Y(), Jl = Y(), Yl = Y(), Xl = Y(Yl), Zl = Y(), X = {
	comment: Rl,
	lineComment: Y(Rl),
	blockComment: Y(Rl),
	docComment: Y(Rl),
	name: zl,
	variableName: Y(zl),
	typeName: Bl,
	tagName: Y(Bl),
	propertyName: Vl,
	attributeName: Y(Vl),
	className: Y(zl),
	labelName: Y(zl),
	namespace: Y(zl),
	macroName: Y(zl),
	literal: Hl,
	string: Ul,
	docString: Y(Ul),
	character: Y(Ul),
	attributeValue: Y(Ul),
	number: Wl,
	integer: Y(Wl),
	float: Y(Wl),
	bool: Y(Hl),
	regexp: Y(Hl),
	escape: Y(Hl),
	color: Y(Hl),
	url: Y(Hl),
	keyword: ql,
	self: Y(ql),
	null: Y(ql),
	atom: Y(ql),
	unit: Y(ql),
	modifier: Y(ql),
	operatorKeyword: Y(ql),
	controlKeyword: Y(ql),
	definitionKeyword: Y(ql),
	moduleKeyword: Y(ql),
	operator: Jl,
	derefOperator: Y(Jl),
	arithmeticOperator: Y(Jl),
	logicOperator: Y(Jl),
	bitwiseOperator: Y(Jl),
	compareOperator: Y(Jl),
	updateOperator: Y(Jl),
	definitionOperator: Y(Jl),
	typeOperator: Y(Jl),
	controlOperator: Y(Jl),
	punctuation: Yl,
	separator: Y(Yl),
	bracket: Xl,
	angleBracket: Y(Xl),
	squareBracket: Y(Xl),
	paren: Y(Xl),
	brace: Y(Xl),
	content: Gl,
	heading: Kl,
	heading1: Y(Kl),
	heading2: Y(Kl),
	heading3: Y(Kl),
	heading4: Y(Kl),
	heading5: Y(Kl),
	heading6: Y(Kl),
	contentSeparator: Y(Gl),
	list: Y(Gl),
	quote: Y(Gl),
	emphasis: Y(Gl),
	strong: Y(Gl),
	link: Y(Gl),
	monospace: Y(Gl),
	strikethrough: Y(Gl),
	inserted: Y(),
	deleted: Y(),
	changed: Y(),
	invalid: Y(),
	meta: Zl,
	documentMeta: Y(Zl),
	annotation: Y(Zl),
	processingInstruction: Y(Zl),
	definition: Tl.defineModifier("definition"),
	constant: Tl.defineModifier("constant"),
	function: Tl.defineModifier("function"),
	standard: Tl.defineModifier("standard"),
	local: Tl.defineModifier("local"),
	special: Tl.defineModifier("special")
};
for (let e in X) {
	let t = X[e];
	t instanceof Tl && (t.name = e);
}
Nl([
	{
		tag: X.link,
		class: "tok-link"
	},
	{
		tag: X.heading,
		class: "tok-heading"
	},
	{
		tag: X.emphasis,
		class: "tok-emphasis"
	},
	{
		tag: X.strong,
		class: "tok-strong"
	},
	{
		tag: X.keyword,
		class: "tok-keyword"
	},
	{
		tag: X.atom,
		class: "tok-atom"
	},
	{
		tag: X.bool,
		class: "tok-bool"
	},
	{
		tag: X.url,
		class: "tok-url"
	},
	{
		tag: X.labelName,
		class: "tok-labelName"
	},
	{
		tag: X.inserted,
		class: "tok-inserted"
	},
	{
		tag: X.deleted,
		class: "tok-deleted"
	},
	{
		tag: X.literal,
		class: "tok-literal"
	},
	{
		tag: X.string,
		class: "tok-string"
	},
	{
		tag: X.number,
		class: "tok-number"
	},
	{
		tag: [
			X.regexp,
			X.escape,
			X.special(X.string)
		],
		class: "tok-string2"
	},
	{
		tag: X.variableName,
		class: "tok-variableName"
	},
	{
		tag: X.local(X.variableName),
		class: "tok-variableName tok-local"
	},
	{
		tag: X.definition(X.variableName),
		class: "tok-variableName tok-definition"
	},
	{
		tag: X.special(X.variableName),
		class: "tok-variableName2"
	},
	{
		tag: X.definition(X.propertyName),
		class: "tok-propertyName tok-definition"
	},
	{
		tag: X.typeName,
		class: "tok-typeName"
	},
	{
		tag: X.namespace,
		class: "tok-namespace"
	},
	{
		tag: X.className,
		class: "tok-className"
	},
	{
		tag: X.macroName,
		class: "tok-macroName"
	},
	{
		tag: X.propertyName,
		class: "tok-propertyName"
	},
	{
		tag: X.operator,
		class: "tok-operator"
	},
	{
		tag: X.comment,
		class: "tok-comment"
	},
	{
		tag: X.meta,
		class: "tok-meta"
	},
	{
		tag: X.invalid,
		class: "tok-invalid"
	},
	{
		tag: X.punctuation,
		class: "tok-punctuation"
	}
]);
//#endregion
//#region node_modules/@codemirror/language/dist/index.js
var Ql, $l = /*@__PURE__*/ new n();
function eu(e) {
	return O.define({ combine: e ? (t) => t.concat(e) : void 0 });
}
var tu = /*@__PURE__*/ new n(), nu = class {
	constructor(e, t, n = [], r = "") {
		this.data = e, this.name = r, N.prototype.hasOwnProperty("tree") || Object.defineProperty(N.prototype, "tree", { get() {
			return Z(this);
		} }), this.parser = t, this.extension = [fu.of(this), N.languageData.of((e, t, n) => {
			let r = ru(e, t, n), i = r.type.prop($l);
			if (!i) return [];
			let a = e.facet(i), o = r.type.prop(tu);
			if (o) {
				let i = r.resolve(t - r.from, n);
				for (let t of o) if (t.test(i, e)) {
					let n = e.facet(t.facet);
					return t.type == "replace" ? n : n.concat(a);
				}
			}
			return a;
		})].concat(n);
	}
	isActiveAt(e, t, n = -1) {
		return ru(e, t, n).type.prop($l) == this.data;
	}
	findRegions(e) {
		let t = e.facet(fu);
		if ((t == null ? void 0 : t.data) == this.data) return [{
			from: 0,
			to: e.doc.length
		}];
		if (!t || !t.allowsNesting) return [];
		let r = [], i = (e, t) => {
			if (e.prop($l) == this.data) {
				r.push({
					from: t,
					to: t + e.length
				});
				return;
			}
			let a = e.prop(n.mounted);
			if (a) {
				if (a.tree.prop($l) == this.data) {
					if (a.overlay) for (let e of a.overlay) r.push({
						from: e.from + t,
						to: e.to + t
					});
					else r.push({
						from: t,
						to: t + e.length
					});
					return;
				}
				if (a.overlay) {
					let e = r.length;
					if (i(a.tree, a.overlay[0].from + t), r.length > e) return;
				}
			}
			for (let n = 0; n < e.children.length; n++) {
				let r = e.children[n];
				r instanceof u && i(r, e.positions[n] + t);
			}
		};
		return i(Z(e), 0), r;
	}
	get allowsNesting() {
		return !0;
	}
};
nu.setState = /*@__PURE__*/ A.define();
function ru(e, t, n) {
	let r = e.facet(fu), i = Z(e).topNode;
	if (!r || r.allowsNesting) for (let e = i; e; e = e.enter(t, n, l.ExcludeBuffers | l.EnterBracketed)) e.type.isTop && (i = e);
	return i;
}
function Z(e) {
	let t = e.field(nu.state, !1);
	return t ? t.tree : u.empty;
}
var iu = class {
	constructor(e) {
		this.doc = e, this.cursorPos = 0, this.string = "", this.cursor = e.iter();
	}
	get length() {
		return this.doc.length;
	}
	syncTo(e) {
		return this.string = this.cursor.next(e - this.cursorPos).value, this.cursorPos = e + this.string.length, this.cursorPos - this.string.length;
	}
	chunk(e) {
		return this.syncTo(e), this.string;
	}
	get lineChunks() {
		return !0;
	}
	read(e, t) {
		let n = this.cursorPos - this.string.length;
		return e < n || t >= this.cursorPos ? this.doc.sliceString(e, t) : this.string.slice(e - n, t - n);
	}
}, au = null, ou = class e {
	constructor(e, t, n = [], r, i, a, o, s) {
		this.parser = e, this.state = t, this.fragments = n, this.tree = r, this.treeLen = i, this.viewport = a, this.skipped = o, this.scheduleOn = s, this.parse = null, this.tempSkipped = [];
	}
	static create(t, n, r) {
		return new e(t, n, [], u.empty, 0, r, [], null);
	}
	startParse() {
		return this.parser.startParse(new iu(this.state.doc), this.fragments);
	}
	work(e, t) {
		return t != null && t >= this.state.doc.length && (t = void 0), this.tree != u.empty && this.isDone(t == null ? this.state.doc.length : t) ? (this.takeTree(), !0) : this.withContext(() => {
			var n;
			if (typeof e == "number") {
				let t = Date.now() + e;
				e = () => Date.now() > t;
			}
			for (this.parse || (this.parse = this.startParse()), t != null && (this.parse.stoppedAt == null || this.parse.stoppedAt > t) && t < this.state.doc.length && this.parse.stopAt(t);;) {
				let r = this.parse.advance();
				if (r) {
					if (this.fragments = this.withoutTempSkipped(se.addTree(r, this.fragments, this.parse.stoppedAt != null)), this.treeLen = (n = this.parse.stoppedAt) == null ? this.state.doc.length : n, this.tree = r, this.parse = null, this.treeLen < (t == null ? this.state.doc.length : t)) this.parse = this.startParse();
					else return !0;
				}
				if (e()) return !1;
			}
		});
	}
	takeTree() {
		let e, t;
		this.parse && (e = this.parse.parsedPos) >= this.treeLen && ((this.parse.stoppedAt == null || this.parse.stoppedAt > e) && this.parse.stopAt(e), this.withContext(() => {
			for (; !(t = this.parse.advance()););
		}), this.treeLen = e, this.tree = t, this.fragments = this.withoutTempSkipped(se.addTree(this.tree, this.fragments, !0)), this.parse = null);
	}
	withContext(e) {
		let t = au;
		au = this;
		try {
			return e();
		} finally {
			au = t;
		}
	}
	withoutTempSkipped(e) {
		for (let t; t = this.tempSkipped.pop();) e = su(e, t.from, t.to);
		return e;
	}
	changes(t, n) {
		let { fragments: r, tree: i, treeLen: a, viewport: o, skipped: s } = this;
		if (this.takeTree(), !t.empty) {
			let e = [];
			if (t.iterChangedRanges((t, n, r, i) => e.push({
				fromA: t,
				toA: n,
				fromB: r,
				toB: i
			})), r = se.applyChanges(r, e), i = u.empty, a = 0, o = {
				from: t.mapPos(o.from, -1),
				to: t.mapPos(o.to, 1)
			}, this.skipped.length) {
				s = [];
				for (let e of this.skipped) {
					let n = t.mapPos(e.from, 1), r = t.mapPos(e.to, -1);
					n < r && s.push({
						from: n,
						to: r
					});
				}
			}
		}
		return new e(this.parser, n, r, i, a, o, s, this.scheduleOn);
	}
	updateViewport(e) {
		if (this.viewport.from == e.from && this.viewport.to == e.to) return !1;
		this.viewport = e;
		let t = this.skipped.length;
		for (let t = 0; t < this.skipped.length; t++) {
			let { from: n, to: r } = this.skipped[t];
			n < e.to && r > e.from && (this.fragments = su(this.fragments, n, r), this.skipped.splice(t--, 1));
		}
		return this.skipped.length >= t ? !1 : (this.reset(), !0);
	}
	reset() {
		this.parse && (this.takeTree(), this.parse = null);
	}
	skipUntilInView(e, t) {
		this.skipped.push({
			from: e,
			to: t
		});
	}
	static getSkippingParser(e) {
		return new class extends ce {
			createParse(t, n, r) {
				let i = r[0].from, o = r[r.length - 1].to;
				return {
					parsedPos: i,
					advance() {
						let t = au;
						if (t) {
							for (let e of r) t.tempSkipped.push(e);
							e && (t.scheduleOn = t.scheduleOn ? Promise.all([t.scheduleOn, e]) : e);
						}
						return this.parsedPos = o, new u(a.none, [], [], o - i);
					},
					stoppedAt: null,
					stopAt() {}
				};
			}
		}();
	}
	isDone(e) {
		e = Math.min(e, this.state.doc.length);
		let t = this.fragments;
		return this.treeLen >= e && t.length && t[0].from == 0 && t[0].to >= e;
	}
	static get() {
		return au;
	}
};
function su(e, t, n) {
	return se.applyChanges(e, [{
		fromA: t,
		toA: n,
		fromB: t,
		toB: n
	}]);
}
var cu = class e {
	constructor(e) {
		this.context = e, this.tree = e.tree;
	}
	apply(t) {
		if (!t.docChanged && this.tree == this.context.tree) return this;
		let n = this.context.changes(t.changes, t.state), r = this.context.treeLen == t.startState.doc.length ? void 0 : Math.max(t.changes.mapPos(this.context.treeLen), n.viewport.to);
		return n.work(20, r) || n.takeTree(), new e(n);
	}
	static init(t) {
		let n = Math.min(3e3, t.doc.length), r = ou.create(t.facet(fu).parser, t, {
			from: 0,
			to: n
		});
		return r.work(20, n) || r.takeTree(), new e(r);
	}
};
nu.state = /*@__PURE__*/ k.define({
	create: cu.init,
	update(e, t) {
		for (let e of t.effects) if (e.is(nu.setState)) return e.value;
		return t.startState.facet(fu) == t.state.facet(fu) ? e.apply(t) : cu.init(t.state);
	}
});
var lu = (e) => {
	let t = setTimeout(() => e(), 500);
	return () => clearTimeout(t);
};
typeof requestIdleCallback < "u" && (lu = (e) => {
	let t = -1, n = setTimeout(() => {
		t = requestIdleCallback(e, { timeout: 400 });
	}, 100);
	return () => t < 0 ? clearTimeout(n) : cancelIdleCallback(t);
});
var uu = typeof navigator < "u" && (Ql = navigator.scheduling) != null && Ql.isInputPending ? () => navigator.scheduling.isInputPending() : null, du = /*@__PURE__*/ W.fromClass(class {
	constructor(e) {
		this.view = e, this.working = null, this.workScheduled = 0, this.chunkEnd = -1, this.chunkBudget = -1, this.work = this.work.bind(this), this.scheduleWork();
	}
	update(e) {
		let t = this.view.state.field(nu.state).context;
		(t.updateViewport(e.view.viewport) || this.view.viewport.to > t.treeLen) && this.scheduleWork(), (e.docChanged || e.selectionSet) && (this.view.hasFocus && (this.chunkBudget += 50), this.scheduleWork()), this.checkAsyncSchedule(t);
	}
	scheduleWork() {
		if (this.working) return;
		let { state: e } = this.view, t = e.field(nu.state);
		(t.tree != t.context.tree || !t.context.isDone(e.doc.length)) && (this.working = lu(this.work));
	}
	work(e) {
		this.working = null;
		let t = Date.now();
		if (this.chunkEnd < t && (this.chunkEnd < 0 || this.view.hasFocus) && (this.chunkEnd = t + 3e4, this.chunkBudget = 3e3), this.chunkBudget <= 0) return;
		let { state: n, viewport: { to: r } } = this.view, i = n.field(nu.state);
		if (i.tree == i.context.tree && i.context.isDone(r + 1e5)) return;
		let a = Date.now() + Math.min(this.chunkBudget, 100, e && !uu ? Math.max(25, e.timeRemaining() - 5) : 1e9), o = i.context.treeLen < r && n.doc.length > r + 1e3, s = i.context.work(() => uu && uu() || Date.now() > a, r + (o ? 0 : 1e5));
		this.chunkBudget -= Date.now() - t, (s || this.chunkBudget <= 0) && (i.context.takeTree(), this.view.dispatch({ effects: nu.setState.of(new cu(i.context)) })), this.chunkBudget > 0 && !(s && !o) && this.scheduleWork(), this.checkAsyncSchedule(i.context);
	}
	checkAsyncSchedule(e) {
		e.scheduleOn && (this.workScheduled++, e.scheduleOn.then(() => this.scheduleWork()).catch((e) => U(this.view.state, e)).then(() => this.workScheduled--), e.scheduleOn = null);
	}
	destroy() {
		this.working && this.working();
	}
	isWorking() {
		return !!(this.working || this.workScheduled > 0);
	}
}, { eventHandlers: { focus() {
	this.scheduleWork();
} } }), fu = /*@__PURE__*/ O.define({
	combine(e) {
		return e.length ? e[0] : null;
	},
	enables: (e) => [
		nu.state,
		du,
		J.contentAttributes.compute([e], (t) => {
			let n = t.facet(e);
			return n && n.name ? { "data-language": n.name } : {};
		})
	]
}), pu = /*@__PURE__*/ O.define(), mu = /*@__PURE__*/ O.define({ combine: (e) => {
	if (!e.length) return "  ";
	let t = e[0];
	if (!t || /\S/.test(t) || Array.from(t).some((e) => e != t[0])) throw Error("Invalid indent unit: " + JSON.stringify(e[0]));
	return t;
} });
function hu(e) {
	let t = e.facet(mu);
	return t.charCodeAt(0) == 9 ? e.tabSize * t.length : t.length;
}
function gu(e, t) {
	let n = "", r = e.tabSize, i = e.facet(mu)[0];
	if (i == "	") {
		for (; t >= r;) n += "	", t -= r;
		i = " ";
	}
	for (let e = 0; e < t; e++) n += i;
	return n;
}
function _u(e, t) {
	e instanceof N && (e = new vu(e));
	for (let n of e.state.facet(pu)) {
		let r = n(e, t);
		if (r !== void 0) return r;
	}
	let n = Z(e.state);
	return n.length >= t ? bu(e, n, t) : null;
}
var vu = class {
	constructor(e, t = {}) {
		this.state = e, this.options = t, this.unit = hu(e);
	}
	lineAt(e, t = 1) {
		let n = this.state.doc.lineAt(e), { simulateBreak: r, simulateDoubleBreak: i } = this.options;
		return r != null && r >= n.from && r <= n.to ? i && r == e ? {
			text: "",
			from: e
		} : (t < 0 ? r < e : r <= e) ? {
			text: n.text.slice(r - n.from),
			from: r
		} : {
			text: n.text.slice(0, r - n.from),
			from: n.from
		} : n;
	}
	textAfterPos(e, t = 1) {
		if (this.options.simulateDoubleBreak && e == this.options.simulateBreak) return "";
		let { text: n, from: r } = this.lineAt(e, t);
		return n.slice(e - r, Math.min(n.length, e + 100 - r));
	}
	column(e, t = 1) {
		let { text: n, from: r } = this.lineAt(e, t), i = this.countColumn(n, e - r), a = this.options.overrideIndentation ? this.options.overrideIndentation(r) : -1;
		return a > -1 && (i += a - this.countColumn(n, n.search(/\S|$/))), i;
	}
	countColumn(e, t = e.length) {
		return Xt(e, this.state.tabSize, t);
	}
	lineIndent(e, t = 1) {
		let { text: n, from: r } = this.lineAt(e, t), i = this.options.overrideIndentation;
		if (i) {
			let e = i(r);
			if (e > -1) return e;
		}
		return this.countColumn(n, n.search(/\S|$/));
	}
	get simulatedBreak() {
		return this.options.simulateBreak || null;
	}
}, yu = /*@__PURE__*/ new n();
function bu(e, t, n) {
	let r = t.resolveStack(n), i = t.resolveInner(n, -1).resolve(n, 0).enterUnfinishedNodesBefore(n);
	if (i != r.node) {
		let e = [];
		for (let t = i; t && !(t.from < r.node.from || t.to > r.node.to || t.from == r.node.from && t.type == r.node.type); t = t.parent) e.push(t);
		for (let t = e.length - 1; t >= 0; t--) r = {
			node: e[t],
			next: r
		};
	}
	return xu(r, e, n);
}
function xu(e, t, n) {
	for (let r = e; r; r = r.next) {
		let e = Cu(r.node);
		if (e) return e(Tu.create(t, n, r));
	}
	return 0;
}
function Su(e) {
	return e.pos == e.options.simulateBreak && e.options.simulateDoubleBreak;
}
function Cu(e) {
	let t = e.type.prop(yu);
	if (t) return t;
	let r = e.firstChild, i;
	if (r && (i = r.type.prop(n.closedBy))) {
		let t = e.lastChild, n = t && i.indexOf(t.name) > -1;
		return (e) => Ou(e, !0, 1, void 0, n && !Su(e) ? t.from : void 0);
	}
	return e.parent == null ? wu : null;
}
function wu() {
	return 0;
}
var Tu = class e extends vu {
	constructor(e, t, n) {
		super(e.state, e.options), this.base = e, this.pos = t, this.context = n;
	}
	get node() {
		return this.context.node;
	}
	static create(t, n, r) {
		return new e(t, n, r);
	}
	get textAfter() {
		return this.textAfterPos(this.pos);
	}
	get baseIndent() {
		return this.baseIndentFor(this.node);
	}
	baseIndentFor(e) {
		let t = this.state.doc.lineAt(e.from);
		for (;;) {
			let n = e.resolve(t.from);
			for (; n.parent && n.parent.from == n.from;) n = n.parent;
			if (Eu(n, e)) break;
			t = this.state.doc.lineAt(n.from);
		}
		return this.lineIndent(t.from);
	}
	continue() {
		return xu(this.context.next, this.base, this.pos);
	}
};
function Eu(e, t) {
	for (let n = t; n; n = n.parent) if (e == n) return !0;
	return !1;
}
function Du(e) {
	let t = e.node, n = t.childAfter(t.from), r = t.lastChild;
	if (!n) return null;
	let i = e.options.simulateBreak, a = e.state.doc.lineAt(n.from), o = i == null || i <= a.from ? a.to : Math.min(a.to, i);
	for (let e = n.to;;) {
		let i = t.childAfter(e);
		if (!i || i == r) return null;
		if (!i.type.isSkipped) {
			if (i.from >= o) return null;
			let e = /^ */.exec(a.text.slice(n.to - a.from))[0].length;
			return {
				from: n.from,
				to: n.to + e
			};
		}
		e = i.to;
	}
}
function Ou(e, t, n, r, i) {
	let a = e.textAfter, o = a.match(/^\s*/)[0].length, s = r && a.slice(o, o + r.length) == r || i == e.pos + o, c = t ? Du(e) : null;
	return c ? s ? e.column(c.from) : e.column(c.to) : e.baseIndent + (s ? 0 : e.unit * n);
}
var ku = 200;
function Au() {
	return N.transactionFilter.of((e) => {
		if (!e.docChanged || !e.isUserEvent("input.type") && !e.isUserEvent("input.complete")) return e;
		let t = e.startState.languageDataAt("indentOnInput", e.startState.selection.main.head);
		if (!t.length) return e;
		let n = e.newDoc, { head: r } = e.newSelection.main, i = n.lineAt(r);
		if (r > i.from + ku) return e;
		let a = n.sliceString(i.from, r);
		if (!t.some((e) => e.test(a))) return e;
		let { state: o } = e, s = -1, c = [];
		for (let { head: e } of o.selection.ranges) {
			let t = o.doc.lineAt(e);
			if (t.from == s) continue;
			s = t.from;
			let n = _u(o, t.from);
			if (n == null) continue;
			let r = /^\s*/.exec(t.text)[0], i = gu(o, n);
			r != i && c.push({
				from: t.from,
				to: t.from + r.length,
				insert: i
			});
		}
		return c.length ? [e, {
			changes: c,
			sequential: !0
		}] : e;
	});
}
var ju = /*@__PURE__*/ O.define(), Mu = /*@__PURE__*/ new n();
function Nu(e, t, n) {
	let r = Z(e);
	if (r.length < n) return null;
	let i = r.resolveStack(n, 1), a = null;
	for (let o = i; o; o = o.next) {
		let i = o.node;
		if (i.to <= n || i.from > n) continue;
		if (a && i.from < t) break;
		let s = i.type.prop(Mu);
		if (s && (i.to < r.length - 50 || r.length == e.doc.length || !Pu(i))) {
			let r = s(i, e);
			r && r.from <= n && r.from >= t && r.to > n && (a = r);
		}
	}
	return a;
}
function Pu(e) {
	let t = e.lastChild;
	return t && t.to == e.to && t.type.isError;
}
function Fu(e, t, n) {
	for (let r of e.facet(ju)) {
		let i = r(e, t, n);
		if (i) return i;
	}
	return Nu(e, t, n);
}
function Iu(e, t) {
	let n = t.mapPos(e.from, 1), r = t.mapPos(e.to, -1);
	return n >= r ? void 0 : {
		from: n,
		to: r
	};
}
var Lu = /*@__PURE__*/ A.define({ map: Iu }), Ru = /*@__PURE__*/ A.define({ map: Iu });
function zu(e) {
	let t = [];
	for (let { head: n } of e.state.selection.ranges) t.some((e) => e.from <= n && e.to >= n) || t.push(e.lineBlockAt(n));
	return t;
}
var Bu = /*@__PURE__*/ k.define({
	create() {
		return B.none;
	},
	update(e, t) {
		t.isUserEvent("delete") && t.changes.iterChangedRanges((t, n) => e = Vu(e, t, n)), e = e.map(t.changes);
		let n = [];
		for (let r of t.effects) r.is(Lu) && !Uu(e, r.value.from, r.value.to) ? n.push(r.value) : r.is(Ru) && (e = e.update({
			filter: (e, t) => r.value.from != e || r.value.to != t,
			filterFrom: r.value.from,
			filterTo: r.value.to
		}));
		if (n.length) {
			let { preparePlaceholder: r } = t.state.facet(Xu), i = n.map((e) => (r ? B.replace({ widget: new ed(r(t.state, e)) }) : $u).range(e.from, e.to));
			e = e.update({ add: i });
		}
		return t.selection && (e = Vu(e, t.selection.main.head)), e;
	},
	provide: (e) => J.decorations.from(e),
	toJSON(e, t) {
		let n = [];
		return e.between(0, t.doc.length, (e, t) => {
			n.push(e, t);
		}), n;
	},
	fromJSON(e) {
		if (!Array.isArray(e) || e.length % 2) throw RangeError("Invalid JSON for fold state");
		let t = [];
		for (let n = 0; n < e.length;) {
			let r = e[n++], i = e[n++];
			if (typeof r != "number" || typeof i != "number") throw RangeError("Invalid JSON for fold state");
			t.push($u.range(r, i));
		}
		return B.set(t, !0);
	}
});
function Vu(e, t, n = t) {
	let r = !1;
	return e.between(t, n, (e, i) => {
		e < n && i > t && (r = !0);
	}), r ? e.update({
		filterFrom: t,
		filterTo: n,
		filter: (e, r) => e >= n || r <= t
	}) : e;
}
function Hu(e, t, n) {
	var r;
	let i = null;
	return (r = e.field(Bu, !1)) == null || r.between(t, n, (e, t) => {
		(!i || i.from > e) && (i = {
			from: e,
			to: t
		});
	}), i;
}
function Uu(e, t, n) {
	let r = !1;
	return e.between(t, t, (e, i) => {
		e == t && i == n && (r = !0);
	}), r;
}
function Wu(e, t) {
	return e.field(Bu, !1) ? t : t.concat(A.appendConfig.of(Zu()));
}
var Gu = (e) => {
	for (let t of zu(e)) {
		let n = Fu(e.state, t.from, t.to);
		if (n) return e.dispatch({ effects: Wu(e.state, [Lu.of(n), qu(e, n)]) }), !0;
	}
	return !1;
}, Ku = (e) => {
	if (!e.state.field(Bu, !1)) return !1;
	let t = [];
	for (let n of zu(e)) {
		let r = Hu(e.state, n.from, n.to);
		r && t.push(Ru.of(r), qu(e, r, !1));
	}
	return t.length && e.dispatch({ effects: t }), t.length > 0;
};
function qu(e, t, n = !0) {
	let r = e.state.doc.lineAt(t.from).number, i = e.state.doc.lineAt(t.to).number;
	return J.announce.of(`${e.state.phrase(n ? "Folded lines" : "Unfolded lines")} ${r} ${e.state.phrase("to")} ${i}.`);
}
var Ju = [
	{
		key: "Ctrl-Shift-[",
		mac: "Cmd-Alt-[",
		run: Gu
	},
	{
		key: "Ctrl-Shift-]",
		mac: "Cmd-Alt-]",
		run: Ku
	},
	{
		key: "Ctrl-Alt-[",
		run: (e) => {
			let { state: t } = e, n = [];
			for (let r = 0; r < t.doc.length;) {
				let i = e.lineBlockAt(r), a = Fu(t, i.from, i.to);
				a && n.push(Lu.of(a)), r = (a ? e.lineBlockAt(a.to) : i).to + 1;
			}
			return n.length && e.dispatch({ effects: Wu(e.state, n) }), !!n.length;
		}
	},
	{
		key: "Ctrl-Alt-]",
		run: (e) => {
			let t = e.state.field(Bu, !1);
			if (!t || !t.size) return !1;
			let n = [];
			return t.between(0, e.state.doc.length, (e, t) => {
				n.push(Ru.of({
					from: e,
					to: t
				}));
			}), e.dispatch({ effects: n }), !0;
		}
	}
], Yu = {
	placeholderDOM: null,
	preparePlaceholder: null,
	placeholderText: "…"
}, Xu = /*@__PURE__*/ O.define({ combine(e) {
	return Mt(e, Yu);
} });
function Zu(e) {
	let t = [Bu, id];
	return e && t.push(Xu.of(e)), t;
}
function Qu(e, t) {
	let { state: n } = e, r = n.facet(Xu), i = (t) => {
		let n = e.lineBlockAt(e.posAtDOM(t.target)), r = Hu(e.state, n.from, n.to);
		r && e.dispatch({ effects: Ru.of(r) }), t.preventDefault();
	};
	if (r.placeholderDOM) return r.placeholderDOM(e, i, t);
	let a = document.createElement("span");
	return a.textContent = r.placeholderText, a.setAttribute("aria-label", n.phrase("folded code")), a.title = n.phrase("unfold"), a.className = "cm-foldPlaceholder", a.onclick = i, a;
}
var $u = /*@__PURE__*/ B.replace({ widget: /*@__PURE__*/ new class extends Fn {
	toDOM(e) {
		return Qu(e, null);
	}
}() }), ed = class extends Fn {
	constructor(e) {
		super(), this.value = e;
	}
	eq(e) {
		return this.value == e.value;
	}
	toDOM(e) {
		return Qu(e, this.value);
	}
}, td = {
	openText: "⌄",
	closedText: "›",
	markerDOM: null,
	domEventHandlers: {},
	foldingChanged: () => !1
}, nd = class extends Qc {
	constructor(e, t) {
		super(), this.config = e, this.open = t;
	}
	eq(e) {
		return this.config == e.config && this.open == e.open;
	}
	toDOM(e) {
		if (this.config.markerDOM) return this.config.markerDOM(this.open);
		let t = document.createElement("span");
		return t.textContent = this.open ? this.config.openText : this.config.closedText, t.title = e.state.phrase(this.open ? "Fold line" : "Unfold line"), t;
	}
};
function rd(e = {}) {
	let t = vn(vn({}, td), e), n = new nd(t, !0), r = new nd(t, !1), i = W.fromClass(class {
		constructor(e) {
			this.from = e.viewport.from, this.markers = this.buildMarkers(e);
		}
		update(e) {
			(e.docChanged || e.viewportChanged || e.startState.facet(fu) != e.state.facet(fu) || e.startState.field(Bu, !1) != e.state.field(Bu, !1) || Z(e.startState) != Z(e.state) || t.foldingChanged(e)) && (this.markers = this.buildMarkers(e.view));
		}
		buildMarkers(e) {
			let t = new zt();
			for (let i of e.viewportLineBlocks) {
				let a = Hu(e.state, i.from, i.to) ? r : Fu(e.state, i.from, i.to) ? n : null;
				a && t.add(i.from, i.from, a);
			}
			return t.finish();
		}
	}), { domEventHandlers: a } = t;
	return [
		i,
		rl({
			class: "cm-foldGutter",
			markers(e) {
				var t;
				return ((t = e.plugin(i)) == null ? void 0 : t.markers) || P.empty;
			},
			initialSpacer() {
				return new nd(t, !1);
			},
			domEventHandlers: vn(vn({}, a), {}, { click: (e, t, n) => {
				if (a.click && a.click(e, t, n)) return !0;
				let r = Hu(e.state, t.from, t.to);
				if (r) return e.dispatch({ effects: Ru.of(r) }), !0;
				let i = Fu(e.state, t.from, t.to);
				return i ? (e.dispatch({ effects: Lu.of(i) }), !0) : !1;
			} })
		}),
		Zu()
	];
}
var id = /*@__PURE__*/ J.baseTheme({
	".cm-foldPlaceholder": {
		backgroundColor: "#eee",
		border: "1px solid #ddd",
		color: "#888",
		borderRadius: ".2em",
		margin: "0 1px",
		padding: "0 1px",
		cursor: "pointer"
	},
	".cm-foldGutter span": {
		padding: "0 1px",
		cursor: "pointer"
	}
}), ad = class e {
	constructor(e, t) {
		this.specs = e;
		let n;
		function r(e) {
			let t = nn.newName();
			return (n || (n = Object.create(null)))["." + t] = e, t;
		}
		let i = typeof t.all == "string" ? t.all : t.all ? r(t.all) : void 0, a = t.scope;
		this.scope = a instanceof nu ? (e) => e.prop($l) == a.data : a ? (e) => e == a : void 0, this.style = Nl(e.map((e) => ({
			tag: e.tag,
			class: e.class || r(Object.assign({}, e, { tag: null }))
		})), { all: i }).style, this.module = n ? new nn(n) : null, this.themeType = t.themeType;
	}
	static define(t, n) {
		return new e(t, n || {});
	}
}, od = /*@__PURE__*/ O.define(), sd = /*@__PURE__*/ O.define({ combine(e) {
	return e.length ? [e[0]] : null;
} });
function cd(e) {
	let t = e.facet(od);
	return t.length ? t : e.facet(sd);
}
function ld(e, t) {
	let n = [dd], r;
	return e instanceof ad && (e.module && n.push(J.styleModule.of(e.module)), r = e.themeType), t != null && t.fallback ? n.push(sd.of(e)) : r ? n.push(od.computeN([J.darkTheme], (t) => t.facet(J.darkTheme) == (r == "dark") ? [e] : [])) : n.push(od.of(e)), n;
}
var ud = class {
	constructor(e) {
		this.markCache = Object.create(null), this.tree = Z(e.state), this.decorations = this.buildDeco(e, cd(e.state)), this.decoratedTo = e.viewport.to;
	}
	update(e) {
		let t = Z(e.state), n = cd(e.state), r = n != cd(e.startState), { viewport: i } = e.view, a = e.changes.mapPos(this.decoratedTo, 1);
		t.length < i.to && !r && t.type == this.tree.type && a >= i.to ? (this.decorations = this.decorations.map(e.changes), this.decoratedTo = a) : (t != this.tree || e.viewportChanged || r) && (this.tree = t, this.decorations = this.buildDeco(e.view, n), this.decoratedTo = i.to);
	}
	buildDeco(e, t) {
		if (!t || !this.tree.length) return B.none;
		let n = new zt();
		for (let { from: r, to: i } of e.visibleRanges) Fl(this.tree, t, (e, t, r) => {
			n.add(e, t, this.markCache[r] || (this.markCache[r] = B.mark({ class: r })));
		}, r, i);
		return n.finish();
	}
}, dd = /*@__PURE__*/ nt.high(/*@__PURE__*/ W.fromClass(ud, { decorations: (e) => e.decorations })), fd = /*@__PURE__*/ ad.define([
	{
		tag: X.meta,
		color: "#404740"
	},
	{
		tag: X.link,
		textDecoration: "underline"
	},
	{
		tag: X.heading,
		textDecoration: "underline",
		fontWeight: "bold"
	},
	{
		tag: X.emphasis,
		fontStyle: "italic"
	},
	{
		tag: X.strong,
		fontWeight: "bold"
	},
	{
		tag: X.strikethrough,
		textDecoration: "line-through"
	},
	{
		tag: X.keyword,
		color: "#708"
	},
	{
		tag: [
			X.atom,
			X.bool,
			X.url,
			X.contentSeparator,
			X.labelName
		],
		color: "#219"
	},
	{
		tag: [X.literal, X.inserted],
		color: "#164"
	},
	{
		tag: [X.string, X.deleted],
		color: "#a11"
	},
	{
		tag: [
			X.regexp,
			X.escape,
			/*@__PURE__*/ X.special(X.string)
		],
		color: "#e40"
	},
	{
		tag: /*@__PURE__*/ X.definition(X.variableName),
		color: "#00f"
	},
	{
		tag: /*@__PURE__*/ X.local(X.variableName),
		color: "#30a"
	},
	{
		tag: [X.typeName, X.namespace],
		color: "#085"
	},
	{
		tag: X.className,
		color: "#167"
	},
	{
		tag: [/*@__PURE__*/ X.special(X.variableName), X.macroName],
		color: "#256"
	},
	{
		tag: /*@__PURE__*/ X.definition(X.propertyName),
		color: "#00c"
	},
	{
		tag: X.comment,
		color: "#940"
	},
	{
		tag: X.invalid,
		color: "#f00"
	}
]), pd = /*@__PURE__*/ J.baseTheme({
	"&.cm-focused .cm-matchingBracket": { backgroundColor: "#328c8252" },
	"&.cm-focused .cm-nonmatchingBracket": { backgroundColor: "#bb555544" }
}), md = 1e4, hd = "()[]{}", gd = /*@__PURE__*/ O.define({ combine(e) {
	return Mt(e, {
		afterCursor: !0,
		brackets: hd,
		maxScanDistance: md,
		renderMatch: yd
	});
} }), _d = /*@__PURE__*/ B.mark({ class: "cm-matchingBracket" }), vd = /*@__PURE__*/ B.mark({ class: "cm-nonmatchingBracket" });
function yd(e) {
	let t = [], n = e.matched ? _d : vd;
	return t.push(n.range(e.start.from, e.start.to)), e.end && t.push(n.range(e.end.from, e.end.to)), t;
}
function bd(e) {
	let t = [], n = e.facet(gd);
	for (let r of e.selection.ranges) {
		if (!r.empty) continue;
		let i = Ed(e, r.head, -1, n) || r.head > 0 && Ed(e, r.head - 1, 1, n) || n.afterCursor && (Ed(e, r.head, 1, n) || r.head < e.doc.length && Ed(e, r.head + 1, -1, n));
		i && (t = t.concat(n.renderMatch(i, e)));
	}
	return B.set(t, !0);
}
var xd = [/* @__PURE__ */ W.fromClass(class {
	constructor(e) {
		this.paused = !1, this.decorations = bd(e.state);
	}
	update(e) {
		(e.docChanged || e.selectionSet || this.paused) && (e.view.composing ? (this.decorations = this.decorations.map(e.changes), this.paused = !0) : (this.decorations = bd(e.state), this.paused = !1));
	}
}, { decorations: (e) => e.decorations }), pd];
function Sd(e = {}) {
	return [gd.of(e), xd];
}
var Cd = /*@__PURE__*/ new n();
function wd(e, t, r) {
	let i = e.prop(t < 0 ? n.openedBy : n.closedBy);
	if (i) return i;
	if (e.name.length == 1) {
		let n = r.indexOf(e.name);
		if (n > -1 && n % 2 == +(t < 0)) return [r[n + t]];
	}
	return null;
}
function Td(e) {
	let t = e.type.prop(Cd);
	return t ? t(e.node) : e;
}
function Ed(e, t, n, r = {}) {
	let i = r.maxScanDistance || md, a = r.brackets || hd, o = Z(e), s = o.resolveInner(t, n);
	for (let r = s; r; r = r.parent) {
		let i = wd(r.type, n, a);
		if (i && r.from < r.to) {
			let o = Td(r);
			if (o && (n > 0 ? t >= o.from && t < o.to : t > o.from && t <= o.to)) return Dd(e, t, n, r, o, i, a);
		}
	}
	return Od(e, t, n, o, s.type, i, a);
}
function Dd(e, t, n, r, i, a, o) {
	let s = r.parent, c = {
		from: i.from,
		to: i.to
	}, l = 0, u = s == null ? void 0 : s.cursor();
	if (u && (n < 0 ? u.childBefore(r.from) : u.childAfter(r.to))) do
		if (n < 0 ? u.to <= r.from : u.from >= r.to) {
			if (l == 0 && a.indexOf(u.type.name) > -1 && u.from < u.to) {
				let e = Td(u);
				return {
					start: c,
					end: e ? {
						from: e.from,
						to: e.to
					} : void 0,
					matched: !0
				};
			}
			if (wd(u.type, n, o)) l++;
			else if (wd(u.type, -n, o)) {
				if (l == 0) {
					let e = Td(u);
					return {
						start: c,
						end: e && e.from < e.to ? {
							from: e.from,
							to: e.to
						} : void 0,
						matched: !1
					};
				}
				l--;
			}
		}
	while (n < 0 ? u.prevSibling() : u.nextSibling());
	return {
		start: c,
		matched: !1
	};
}
function Od(e, t, n, r, i, a, o) {
	if (n < 0 ? !t : t == e.doc.length) return null;
	let s = n < 0 ? e.sliceDoc(t - 1, t) : e.sliceDoc(t, t + 1), c = o.indexOf(s);
	if (c < 0 || c % 2 == 0 != n > 0) return null;
	let l = {
		from: n < 0 ? t - 1 : t,
		to: n > 0 ? t + 1 : t
	}, u = e.doc.iterRange(t, n > 0 ? e.doc.length : 0), d = 0;
	for (let e = 0; !u.next().done && e <= a;) {
		let a = u.value;
		n < 0 && (e += a.length);
		let s = t + e * n;
		for (let e = n > 0 ? 0 : a.length - 1, t = n > 0 ? a.length : -1; e != t; e += n) {
			let t = o.indexOf(a[e]);
			if (!(t < 0 || r.resolveInner(s + e, 1).type != i)) {
				if (t % 2 == 0 == n > 0) d++;
				else if (d == 1) return {
					start: l,
					end: {
						from: s + e,
						to: s + e + 1
					},
					matched: t >> 1 == c >> 1
				};
				else d--;
			}
		}
		n > 0 && (e += a.length);
	}
	return u.done ? {
		start: l,
		matched: !1
	} : null;
}
function kd(e, t, n, r = 0, i = 0) {
	t == null && (t = e.search(/[^\s\u00a0]/), t == -1 && (t = e.length));
	let a = i;
	for (let i = r; i < t; i++) e.charCodeAt(i) == 9 ? a += n - a % n : a++;
	return a;
}
var Ad = class {
	constructor(e, t, n, r) {
		this.string = e, this.tabSize = t, this.indentUnit = n, this.overrideIndent = r, this.pos = 0, this.start = 0, this.lastColumnPos = 0, this.lastColumnValue = 0;
	}
	eol() {
		return this.pos >= this.string.length;
	}
	sol() {
		return this.pos == 0;
	}
	peek() {
		return this.string.charAt(this.pos) || void 0;
	}
	next() {
		if (this.pos < this.string.length) return this.string.charAt(this.pos++);
	}
	eat(e) {
		let t = this.string.charAt(this.pos), n;
		if (n = typeof e == "string" ? t == e : t && (e instanceof RegExp ? e.test(t) : e(t)), n) return ++this.pos, t;
	}
	eatWhile(e) {
		let t = this.pos;
		for (; this.eat(e););
		return this.pos > t;
	}
	eatSpace() {
		let e = this.pos;
		for (; /[\s\u00a0]/.test(this.string.charAt(this.pos));) ++this.pos;
		return this.pos > e;
	}
	skipToEnd() {
		this.pos = this.string.length;
	}
	skipTo(e) {
		let t = this.string.indexOf(e, this.pos);
		if (t > -1) return this.pos = t, !0;
	}
	backUp(e) {
		this.pos -= e;
	}
	column() {
		return this.lastColumnPos < this.start && (this.lastColumnValue = kd(this.string, this.start, this.tabSize, this.lastColumnPos, this.lastColumnValue), this.lastColumnPos = this.start), this.lastColumnValue;
	}
	indentation() {
		var e;
		return (e = this.overrideIndent) == null ? kd(this.string, null, this.tabSize) : e;
	}
	match(e, t, n) {
		if (typeof e == "string") {
			let r = (e) => n ? e.toLowerCase() : e;
			return r(this.string.substr(this.pos, e.length)) == r(e) ? (t !== !1 && (this.pos += e.length), !0) : null;
		}
		{
			let n = this.string.slice(this.pos).match(e);
			return n && n.index > 0 ? null : (n && t !== !1 && (this.pos += n[0].length), n);
		}
	}
	current() {
		return this.string.slice(this.start, this.pos);
	}
};
function jd(e) {
	return {
		name: e.name || "",
		token: e.token,
		blankLine: e.blankLine || (() => {}),
		startState: e.startState || (() => !0),
		copyState: e.copyState || Md,
		indent: e.indent || (() => null),
		languageData: e.languageData || {},
		tokenTable: e.tokenTable || Bd,
		mergeTokens: e.mergeTokens !== !1
	};
}
function Md(e) {
	if (typeof e != "object") return e;
	let t = {};
	for (let n in e) {
		let r = e[n];
		t[n] = r instanceof Array ? r.slice() : r;
	}
	return t;
}
var Nd = /*@__PURE__*/ new WeakMap(), Pd = class e extends nu {
	constructor(e) {
		let t = eu(e.languageData), r = jd(e), i, a = new class extends ce {
			createParse(e, t, n) {
				return new Rd(i, e, t, n);
			}
		}();
		super(t, a, [], e.name), this.topNode = Xd(t, this), i = this, this.streamParser = r, this.stateAfter = new n({ perNode: !0 }), this.tokenTable = e.tokenTable ? new Kd(r.tokenTable) : qd;
	}
	static define(t) {
		return new e(t);
	}
	getIndent(e) {
		let t, { overrideIndentation: n } = e.options;
		n && (t = Nd.get(e.state), t != null && t < e.pos - 1e4 && (t = void 0));
		let r = Fd(this, e.node.tree, e.node.from, e.node.from, t == null ? e.pos : t), i, a;
		if (r ? (a = r.state, i = r.pos + 1) : (a = this.streamParser.startState(e.unit), i = e.node.from), e.pos - i > 1e4) return null;
		for (; i < e.pos;) {
			let t = e.state.doc.lineAt(i), r = Math.min(e.pos, t.to);
			if (t.length) {
				let i = n ? n(t.from) : -1, o = new Ad(t.text, e.state.tabSize, e.unit, i < 0 ? void 0 : i);
				for (; o.pos < r - t.from;) zd(this.streamParser.token, o, a);
			} else this.streamParser.blankLine(a, e.unit);
			if (r == e.pos) break;
			i = t.to + 1;
		}
		let o = e.lineAt(e.pos);
		return n && t == null && Nd.set(e.state, o.from), this.streamParser.indent(a, /^\s*(.*)/.exec(o.text)[1], e);
	}
	get allowsNesting() {
		return !1;
	}
};
function Fd(e, t, n, r, i) {
	let a = n >= r && n + t.length <= i && t.prop(e.stateAfter);
	if (a) return {
		state: e.streamParser.copyState(a),
		pos: n + t.length
	};
	for (let a = t.children.length - 1; a >= 0; a--) {
		let o = t.children[a], s = n + t.positions[a], c = o instanceof u && s < i && Fd(e, o, s, r, i);
		if (c) return c;
	}
	return null;
}
function Id(e, t, n, r, i) {
	if (i && n <= 0 && r >= t.length) return t;
	!i && n == 0 && t.type == e.topNode && (i = !0);
	for (let a = t.children.length - 1; a >= 0; a--) {
		let o = t.positions[a], s = t.children[a], c;
		if (o < r && s instanceof u) {
			if (!(c = Id(e, s, n - o, r - o, i))) break;
			return i ? new u(t.type, t.children.slice(0, a).concat(c), t.positions.slice(0, a + 1), o + c.length) : c;
		}
	}
	return null;
}
function Ld(e, t, n, r, i) {
	for (let i of t) {
		let t = i.from + (i.openStart ? 25 : 0), a = i.to - (i.openEnd ? 25 : 0), o = t <= n && a > n && Fd(e, i.tree, 0 - i.offset, n, a), s;
		if (o && o.pos <= r && (s = Id(e, i.tree, n + i.offset, o.pos + i.offset, !1))) return {
			state: o.state,
			tree: s
		};
	}
	return {
		state: e.streamParser.startState(i ? hu(i) : 4),
		tree: u.empty
	};
}
var Rd = class {
	constructor(e, t, n, r) {
		this.lang = e, this.input = t, this.fragments = n, this.ranges = r, this.stoppedAt = null, this.chunks = [], this.chunkPos = [], this.chunk = [], this.chunkReused = void 0, this.rangeIndex = 0, this.to = r[r.length - 1].to;
		let i = ou.get(), a = r[0].from, { state: o, tree: s } = Ld(e, n, a, this.to, i == null ? void 0 : i.state);
		this.state = o, this.parsedPos = this.chunkStart = a + s.length;
		for (let e = 0; e < s.children.length; e++) this.chunks.push(s.children[e]), this.chunkPos.push(s.positions[e]);
		i && this.parsedPos < i.viewport.from - 1e5 && r.some((e) => e.from <= i.viewport.from && e.to >= i.viewport.from) && (this.state = this.lang.streamParser.startState(hu(i.state)), i.skipUntilInView(this.parsedPos, i.viewport.from), this.parsedPos = i.viewport.from), this.moveRangeIndex();
	}
	advance() {
		let e = ou.get(), t = this.stoppedAt == null ? this.to : Math.min(this.to, this.stoppedAt), n = Math.min(t, this.chunkStart + 512);
		for (e && (n = Math.min(n, e.viewport.to)); this.parsedPos < n;) this.parseLine(e);
		return this.chunkStart < this.parsedPos && this.finishChunk(), this.parsedPos >= t ? this.finish() : e && this.parsedPos >= e.viewport.to ? (e.skipUntilInView(this.parsedPos, t), this.finish()) : null;
	}
	stopAt(e) {
		this.stoppedAt = e;
	}
	lineAfter(e) {
		let t = this.input.chunk(e);
		if (this.input.lineChunks) t == "\n" && (t = "");
		else {
			let e = t.indexOf("\n");
			e > -1 && (t = t.slice(0, e));
		}
		return e + t.length <= this.to ? t : t.slice(0, this.to - e);
	}
	nextLine() {
		let e = this.parsedPos, t = this.lineAfter(e), n = e + t.length;
		for (let e = this.rangeIndex;;) {
			let r = this.ranges[e].to;
			if (r >= n || (t = t.slice(0, r - (n - t.length)), e++, e == this.ranges.length)) break;
			let i = this.ranges[e].from, a = this.lineAfter(i);
			t += a, n = i + a.length;
		}
		return {
			line: t,
			end: n
		};
	}
	skipGapsTo(e, t, n) {
		for (;;) {
			let r = this.ranges[this.rangeIndex].to, i = e + t;
			if (n > 0 ? r > i : r >= i) break;
			let a = this.ranges[++this.rangeIndex].from;
			t += a - r;
		}
		return t;
	}
	moveRangeIndex() {
		for (; this.ranges[this.rangeIndex].to < this.parsedPos;) this.rangeIndex++;
	}
	emitToken(e, t, n, r) {
		let i = 4;
		if (this.ranges.length > 1) {
			r = this.skipGapsTo(t, r, 1), t += r;
			let e = this.chunk.length;
			r = this.skipGapsTo(n, r, -1), n += r, i += this.chunk.length - e;
		}
		let a = this.chunk.length - 4;
		return this.lang.streamParser.mergeTokens && i == 4 && a >= 0 && this.chunk[a] == e && this.chunk[a + 2] == t ? this.chunk[a + 2] = n : this.chunk.push(e, t, n, i), r;
	}
	parseLine(e) {
		let { line: t, end: n } = this.nextLine(), r = 0, { streamParser: i } = this.lang, a = new Ad(t, e ? e.state.tabSize : 4, e ? hu(e.state) : 2);
		if (a.eol()) i.blankLine(this.state, a.indentUnit);
		else for (; !a.eol();) {
			let e = zd(i.token, a, this.state);
			if (e && (r = this.emitToken(this.lang.tokenTable.resolve(e), this.parsedPos + a.start, this.parsedPos + a.pos, r)), a.start > 1e4) break;
		}
		this.parsedPos = n, this.moveRangeIndex(), this.parsedPos < this.to && this.parsedPos++;
	}
	finishChunk() {
		let e = u.build({
			buffer: this.chunk,
			start: this.chunkStart,
			length: this.parsedPos - this.chunkStart,
			nodeSet: Hd,
			topID: 0,
			maxBufferLength: 512,
			reused: this.chunkReused
		});
		e = new u(e.type, e.children, e.positions, e.length, [[this.lang.stateAfter, this.lang.streamParser.copyState(this.state)]]), this.chunks.push(e), this.chunkPos.push(this.chunkStart - this.ranges[0].from), this.chunk = [], this.chunkReused = void 0, this.chunkStart = this.parsedPos;
	}
	finish() {
		return new u(this.lang.topNode, this.chunks, this.chunkPos, this.parsedPos - this.ranges[0].from).balance();
	}
};
function zd(e, t, n) {
	t.start = t.pos;
	for (let r = 0; r < 10; r++) {
		let r = e(t, n);
		if (t.pos > t.start) return r;
	}
	throw Error("Stream parser failed to advance stream.");
}
var Bd = /*@__PURE__*/ Object.create(null), Vd = [a.none], Hd = /*@__PURE__*/ new o(Vd), Ud = [], Wd = /*@__PURE__*/ Object.create(null), Gd = /*@__PURE__*/ Object.create(null);
for (let [e, t] of [
	["variable", "variableName"],
	["variable-2", "variableName.special"],
	["string-2", "string.special"],
	["def", "variableName.definition"],
	["tag", "tagName"],
	["attribute", "attributeName"],
	["type", "typeName"],
	["builtin", "variableName.standard"],
	["qualifier", "modifier"],
	["error", "invalid"],
	["header", "heading"],
	["property", "propertyName"]
]) Gd[e] = /*@__PURE__*/ Yd(Bd, t);
var Kd = class {
	constructor(e) {
		this.extra = e, this.table = Object.assign(Object.create(null), Gd);
	}
	resolve(e) {
		return e ? this.table[e] || (this.table[e] = Yd(this.extra, e)) : 0;
	}
}, qd = /*@__PURE__*/ new Kd(Bd);
function Jd(e, t) {
	Ud.indexOf(e) > -1 || (Ud.push(e), console.warn(t));
}
function Yd(e, t) {
	let n = [];
	for (let r of t.split(" ")) {
		let t = [];
		for (let n of r.split(".")) {
			let r = e[n] || X[n];
			r ? typeof r == "function" ? t.length ? t = t.map(r) : Jd(n, `Modifier ${n} used at start of tag`) : t.length ? Jd(n, `Tag ${n} used as modifier`) : t = Array.isArray(r) ? r : [r] : Jd(n, `Unknown highlighting tag ${n}`);
		}
		for (let e of t) n.push(e);
	}
	if (!n.length) return 0;
	let r = t.replace(/ /g, "_"), i = r + " " + n.map((e) => e.id), o = Wd[i];
	if (o) return o.id;
	let s = Wd[i] = a.define({
		id: Vd.length,
		name: r,
		props: [Al({ [r]: n })]
	});
	return Vd.push(s), s.id;
}
function Xd(e, t) {
	let n = a.define({
		id: Vd.length,
		name: "Document",
		props: [$l.add(() => e), yu.add(() => (e) => t.getIndent(e))],
		top: !0
	});
	return Vd.push(n), n;
}
V.RTL, V.LTR;
//#endregion
//#region node_modules/@codemirror/commands/dist/index.js
var Zd = (e) => {
	let { state: t } = e, n = t.doc.lineAt(t.selection.main.from), r = nf(e.state, n.from);
	return r.line ? $d(e) : r.block ? tf(e) : !1;
};
function Qd(e, t) {
	return ({ state: n, dispatch: r }) => {
		if (n.readOnly) return !1;
		let i = e(t, n);
		return i ? (r(n.update(i)), !0) : !1;
	};
}
var $d = /*@__PURE__*/ Qd(cf, 0), ef = /*@__PURE__*/ Qd(sf, 0), tf = /*@__PURE__*/ Qd((e, t) => sf(e, t, of(t)), 0);
function nf(e, t) {
	let n = e.languageDataAt("commentTokens", t, 1);
	return n.length ? n[0] : {};
}
var rf = 50;
function af(e, { open: t, close: n }, r, i) {
	let a = e.sliceDoc(r - rf, r), o = e.sliceDoc(i, i + rf), s = /\s*$/.exec(a)[0].length, c = /^\s*/.exec(o)[0].length, l = a.length - s;
	if (a.slice(l - t.length, l) == t && o.slice(c, c + n.length) == n) return {
		open: {
			pos: r - s,
			margin: s && 1
		},
		close: {
			pos: i + c,
			margin: c && 1
		}
	};
	let u, d;
	i - r <= 100 ? u = d = e.sliceDoc(r, i) : (u = e.sliceDoc(r, r + rf), d = e.sliceDoc(i - rf, i));
	let f = /^\s*/.exec(u)[0].length, p = /\s*$/.exec(d)[0].length, m = d.length - p - n.length;
	return u.slice(f, f + t.length) == t && d.slice(m, m + n.length) == n ? {
		open: {
			pos: r + f + t.length,
			margin: +!!/\s/.test(u.charAt(f + t.length))
		},
		close: {
			pos: i - p - n.length,
			margin: +!!/\s/.test(d.charAt(m - 1))
		}
	} : null;
}
function of(e) {
	let t = [];
	for (let n of e.selection.ranges) {
		let r = e.doc.lineAt(n.from), i = n.to <= r.to ? r : e.doc.lineAt(n.to);
		i.from > r.from && i.from == n.to && (i = n.to == r.to + 1 ? r : e.doc.lineAt(n.to - 1));
		let a = t.length - 1;
		a >= 0 && t[a].to > r.from ? t[a].to = i.to : t.push({
			from: r.from + /^\s*/.exec(r.text)[0].length,
			to: i.to
		});
	}
	return t;
}
function sf(e, t, n = t.selection.ranges) {
	let r = n.map((e) => nf(t, e.from).block);
	if (!r.every((e) => e)) return null;
	let i = n.map((e, n) => af(t, r[n], e.from, e.to));
	if (e != 2 && !i.every((e) => e)) return { changes: t.changes(n.map((e, t) => i[t] ? [] : [{
		from: e.from,
		insert: r[t].open + " "
	}, {
		from: e.to,
		insert: " " + r[t].close
	}])) };
	if (e != 1 && i.some((e) => e)) {
		let e = [];
		for (let t = 0, n; t < i.length; t++) if (n = i[t]) {
			let i = r[t], { open: a, close: o } = n;
			e.push({
				from: a.pos - i.open.length,
				to: a.pos + a.margin
			}, {
				from: o.pos - o.margin,
				to: o.pos + i.close.length
			});
		}
		return { changes: e };
	}
	return null;
}
function cf(e, t, n = t.selection.ranges) {
	let r = [], i = -1;
	ranges: for (let { from: e, to: a } of n) {
		let n = r.length, o = 1e9, s;
		for (let n = e; n <= a;) {
			let c = t.doc.lineAt(n);
			if (s == null && (s = nf(t, c.from).line, !s)) continue ranges;
			if (c.from > i && (e == a || a > c.from)) {
				i = c.from;
				let e = /^\s*/.exec(c.text)[0].length, t = e == c.length, n = c.text.slice(e, e + s.length) == s ? e : -1;
				e < c.text.length && e < o && (o = e), r.push({
					line: c,
					comment: n,
					token: s,
					indent: e,
					empty: t,
					single: !1
				});
			}
			n = c.to + 1;
		}
		if (o < 1e9) for (let e = n; e < r.length; e++) r[e].indent < r[e].line.text.length && (r[e].indent = o);
		r.length == n + 1 && (r[n].single = !0);
	}
	if (e != 2 && r.some((e) => e.comment < 0 && (!e.empty || e.single))) {
		let e = [];
		for (let { line: t, token: n, indent: i, empty: a, single: o } of r) (o || !a) && e.push({
			from: t.from + i,
			insert: n + " "
		});
		let n = t.changes(e);
		return {
			changes: n,
			selection: t.selection.map(n, 1)
		};
	}
	if (e != 1 && r.some((e) => e.comment >= 0)) {
		let e = [];
		for (let { line: t, comment: n, token: i } of r) if (n >= 0) {
			let r = t.from + n, a = r + i.length;
			t.text[a - t.from] == " " && a++, e.push({
				from: r,
				to: a
			});
		}
		return { changes: e };
	}
	return null;
}
var lf = /*@__PURE__*/ _t.define(), uf = /*@__PURE__*/ _t.define(), df = /*@__PURE__*/ O.define(), ff = /*@__PURE__*/ O.define({ combine(e) {
	return Mt(e, {
		minDepth: 100,
		newGroupDelay: 500,
		joinToEvent: (e, t) => t
	}, {
		minDepth: Math.max,
		newGroupDelay: Math.min,
		joinToEvent: (e, t) => (n, r) => e(n, r) || t(n, r)
	});
} }), pf = /*@__PURE__*/ k.define({
	create() {
		return Mf.empty;
	},
	update(e, t) {
		let n = t.state.facet(ff), r = t.annotation(lf);
		if (r) {
			let i = bf.fromTransaction(t, r.selection), a = r.side, o = a == 0 ? e.undone : e.done;
			return o = i ? xf(o, o.length, n.minDepth, i) : Df(o, t.startState.selection), new Mf(a == 0 ? r.rest : o, a == 0 ? o : r.rest);
		}
		let i = t.annotation(uf);
		if ((i == "full" || i == "before") && (e = e.isolate()), t.annotation(j.addToHistory) === !1) return t.changes.empty ? e : e.addMapping(t.changes.desc);
		let a = bf.fromTransaction(t), o = t.annotation(j.time), s = t.annotation(j.userEvent);
		return a ? e = e.addChanges(a, o, s, n, t) : t.selection && (e = e.addSelection(t.startState.selection, o, s, n.newGroupDelay)), (i == "full" || i == "after") && (e = e.isolate()), e;
	},
	toJSON(e) {
		return {
			done: e.done.map((e) => e.toJSON()),
			undone: e.undone.map((e) => e.toJSON())
		};
	},
	fromJSON(e) {
		return new Mf(e.done.map(bf.fromJSON), e.undone.map(bf.fromJSON));
	}
});
function mf(e = {}) {
	return [
		pf,
		ff.of(e),
		J.domEventHandlers({ beforeinput(e, t) {
			let n = e.inputType == "historyUndo" ? gf : e.inputType == "historyRedo" ? _f : null;
			return n ? (e.preventDefault(), n(t)) : !1;
		} })
	];
}
function hf(e, t) {
	return function({ state: n, dispatch: r }) {
		if (!t && n.readOnly) return !1;
		let i = n.field(pf, !1);
		if (!i) return !1;
		let a = i.pop(e, n, t);
		return a ? (r(a), !0) : !1;
	};
}
var gf = /*@__PURE__*/ hf(0, !1), _f = /*@__PURE__*/ hf(1, !1), vf = /*@__PURE__*/ hf(0, !0), yf = /*@__PURE__*/ hf(1, !0), bf = class e {
	constructor(e, t, n, r, i) {
		this.changes = e, this.effects = t, this.mapped = n, this.startSelection = r, this.selectionsAfter = i;
	}
	setSelAfter(t) {
		return new e(this.changes, this.effects, this.mapped, this.startSelection, t);
	}
	toJSON() {
		var e, t, n;
		return {
			changes: (e = this.changes) == null ? void 0 : e.toJSON(),
			mapped: (t = this.mapped) == null ? void 0 : t.toJSON(),
			startSelection: (n = this.startSelection) == null ? void 0 : n.toJSON(),
			selectionsAfter: this.selectionsAfter.map((e) => e.toJSON())
		};
	}
	static fromJSON(t) {
		return new e(t.changes && ze.fromJSON(t.changes), [], t.mapped && Re.fromJSON(t.mapped), t.startSelection && D.fromJSON(t.startSelection), t.selectionsAfter.map(D.fromJSON));
	}
	static fromTransaction(t, n) {
		let r = Tf;
		for (let e of t.startState.facet(df)) {
			let n = e(t);
			n.length && (r = r.concat(n));
		}
		return !r.length && t.changes.empty ? null : new e(t.changes.invert(t.startState.doc), r, void 0, n || t.startState.selection, Tf);
	}
	static selection(t) {
		return new e(void 0, Tf, void 0, void 0, t);
	}
};
function xf(e, t, n, r) {
	let i = t + 1 > n + 20 ? t - n - 1 : 0, a = e.slice(i, t);
	return a.push(r), a;
}
function Sf(e, t) {
	let n = [], r = !1;
	return e.iterChangedRanges((e, t) => n.push(e, t)), t.iterChangedRanges((e, t, i, a) => {
		for (let e = 0; e < n.length;) {
			let t = n[e++], o = n[e++];
			a >= t && i <= o && (r = !0);
		}
	}), r;
}
function Cf(e, t) {
	return e.ranges.length == t.ranges.length && e.ranges.filter((e, n) => e.empty != t.ranges[n].empty).length === 0;
}
function wf(e, t) {
	return e.length ? t.length ? e.concat(t) : e : t;
}
var Tf = [], Ef = 200;
function Df(e, t) {
	if (e.length) {
		let n = e[e.length - 1], r = n.selectionsAfter.slice(Math.max(0, n.selectionsAfter.length - Ef));
		return r.length && r[r.length - 1].eq(t) ? e : (r.push(t), xf(e, e.length - 1, 1e9, n.setSelAfter(r)));
	}
	return [bf.selection([t])];
}
function Of(e) {
	let t = e[e.length - 1], n = e.slice();
	return n[e.length - 1] = t.setSelAfter(t.selectionsAfter.slice(0, t.selectionsAfter.length - 1)), n;
}
function kf(e, t) {
	if (!e.length) return e;
	let n = e.length, r = Tf;
	for (; n;) {
		let i = Af(e[n - 1], t, r);
		if (i.changes && !i.changes.empty || i.effects.length) {
			let t = e.slice(0, n);
			return t[n - 1] = i, t;
		}
		t = i.mapped, n--, r = i.selectionsAfter;
	}
	return r.length ? [bf.selection(r)] : Tf;
}
function Af(e, t, n) {
	let r = wf(e.selectionsAfter.length ? e.selectionsAfter.map((e) => e.map(t)) : Tf, n);
	if (!e.changes) return bf.selection(r);
	let i = e.changes.map(t), a = t.mapDesc(e.changes, !0), o = e.mapped ? e.mapped.composeDesc(a) : a;
	return new bf(i, A.mapEffects(e.effects, t), o, e.startSelection.map(a), r);
}
var jf = /^(input\.type|delete)($|\.)/, Mf = class e {
	constructor(e, t, n = 0, r = void 0) {
		this.done = e, this.undone = t, this.prevTime = n, this.prevUserEvent = r;
	}
	isolate() {
		return this.prevTime ? new e(this.done, this.undone) : this;
	}
	addChanges(t, n, r, i, a) {
		let o = this.done, s = o[o.length - 1];
		return o = s && s.changes && !s.changes.empty && t.changes && (!r || jf.test(r)) && (!s.selectionsAfter.length && n - this.prevTime < i.newGroupDelay && i.joinToEvent(a, Sf(s.changes, t.changes)) || r == "input.type.compose") ? xf(o, o.length - 1, i.minDepth, new bf(t.changes.compose(s.changes), wf(A.mapEffects(t.effects, s.changes), s.effects), s.mapped, s.startSelection, Tf)) : xf(o, o.length, i.minDepth, t), new e(o, Tf, n, r);
	}
	addSelection(t, n, r, i) {
		let a = this.done.length ? this.done[this.done.length - 1].selectionsAfter : Tf;
		return a.length > 0 && n - this.prevTime < i && r == this.prevUserEvent && r && /^select($|\.)/.test(r) && Cf(a[a.length - 1], t) ? this : new e(Df(this.done, t), this.undone, n, r);
	}
	addMapping(t) {
		return new e(kf(this.done, t), kf(this.undone, t), this.prevTime, this.prevUserEvent);
	}
	pop(e, t, n) {
		let r = e == 0 ? this.done : this.undone;
		if (r.length == 0) return null;
		let i = r[r.length - 1], a = i.selectionsAfter[0] || (i.startSelection ? i.startSelection.map(i.changes.invertedDesc, 1) : t.selection);
		if (n && i.selectionsAfter.length) return t.update({
			selection: i.selectionsAfter[i.selectionsAfter.length - 1],
			annotations: lf.of({
				side: e,
				rest: Of(r),
				selection: a
			}),
			userEvent: e == 0 ? "select.undo" : "select.redo",
			scrollIntoView: !0
		});
		if (i.changes) {
			let n = r.length == 1 ? Tf : r.slice(0, r.length - 1);
			return i.mapped && (n = kf(n, i.mapped)), t.update({
				changes: i.changes,
				selection: i.startSelection,
				effects: i.effects,
				annotations: lf.of({
					side: e,
					rest: n,
					selection: a
				}),
				filter: !1,
				userEvent: e == 0 ? "undo" : "redo",
				scrollIntoView: !0
			});
		}
		return null;
	}
};
Mf.empty = /*@__PURE__*/ new Mf(Tf, Tf);
var Nf = [
	{
		key: "Mod-z",
		run: gf,
		preventDefault: !0
	},
	{
		key: "Mod-y",
		mac: "Mod-Shift-z",
		run: _f,
		preventDefault: !0
	},
	{
		linux: "Ctrl-Shift-z",
		run: _f,
		preventDefault: !0
	},
	{
		key: "Mod-u",
		run: vf,
		preventDefault: !0
	},
	{
		key: "Alt-u",
		mac: "Mod-Shift-u",
		run: yf,
		preventDefault: !0
	}
];
function Pf(e, t) {
	return D.create(e.ranges.map(t), e.mainIndex);
}
function Ff(e, t) {
	return e.update({
		selection: t,
		scrollIntoView: !0,
		userEvent: "select"
	});
}
function If({ state: e, dispatch: t }, n) {
	let r = Pf(e.selection, n);
	return !r.eq(e.selection, !0) && (t(Ff(e, r)), !0);
}
function Lf(e, t) {
	return D.cursor(t ? e.to : e.from);
}
function Rf(e, t) {
	return If(e, (n) => n.empty ? e.moveByChar(n, t) : Lf(n, t));
}
function Q(e) {
	return e.textDirectionAt(e.state.selection.main.head) == V.LTR;
}
var zf = (e) => Rf(e, !Q(e)), Bf = (e) => Rf(e, Q(e));
function Vf(e, t) {
	return If(e, (n) => n.empty ? e.moveByGroup(n, t) : Lf(n, t));
}
var Hf = (e) => Vf(e, !Q(e)), Uf = (e) => Vf(e, Q(e));
typeof Intl < "u" && Intl.Segmenter;
function Wf(e, t, n) {
	if (t.type.prop(n)) return !0;
	let r = t.to - t.from;
	return r && (r > 2 || /[^\s,.;:]/.test(e.sliceDoc(t.from, t.to))) || t.firstChild;
}
function Gf(e, t, r) {
	let i = Z(e).resolveInner(t.head), a = r ? n.closedBy : n.openedBy;
	for (let n = t.head;;) {
		let t = r ? i.childAfter(n) : i.childBefore(n);
		if (!t) break;
		Wf(e, t, a) ? i = t : n = r ? t.to : t.from;
	}
	let o = i.type.prop(a), s, c;
	return c = o && (s = r ? Ed(e, i.from, 1) : Ed(e, i.to, -1)) && s.matched ? r ? s.end.to : s.end.from : r ? i.to : i.from, D.cursor(c, r ? -1 : 1);
}
var Kf = (e) => If(e, (t) => Gf(e.state, t, !Q(e))), qf = (e) => If(e, (t) => Gf(e.state, t, Q(e)));
function Jf(e, t) {
	return If(e, (n) => {
		if (!n.empty) return Lf(n, t);
		let r = e.moveVertically(n, t);
		return r.head == n.head ? e.moveToLineBoundary(n, t) : r;
	});
}
var Yf = (e) => Jf(e, !1), Xf = (e) => Jf(e, !0);
function Zf(e) {
	let t = e.scrollDOM.clientHeight < e.scrollDOM.scrollHeight - 2, n = 0, r = 0, i;
	if (t) {
		for (let t of e.state.facet(J.scrollMargins)) {
			let i = t(e);
			i != null && i.top && (n = Math.max(i == null ? void 0 : i.top, n)), i != null && i.bottom && (r = Math.max(i == null ? void 0 : i.bottom, r));
		}
		i = e.scrollDOM.clientHeight - n - r;
	} else i = (e.dom.ownerDocument.defaultView || window).innerHeight;
	return {
		marginTop: n,
		marginBottom: r,
		selfScroll: t,
		height: Math.max(e.defaultLineHeight, i - 5)
	};
}
function Qf(e, t) {
	let n = Zf(e), { state: r } = e, i = Pf(r.selection, (r) => r.empty ? e.moveVertically(r, t, n.height) : Lf(r, t));
	if (i.eq(r.selection)) return !1;
	let a;
	if (n.selfScroll) {
		let t = e.coordsAtPos(r.selection.main.head), o = e.scrollDOM.getBoundingClientRect(), s = o.top + n.marginTop, c = o.bottom - n.marginBottom;
		t && t.top > s && t.bottom < c && (a = J.scrollIntoView(i.main.head, {
			y: "start",
			yMargin: t.top - s
		}));
	}
	return e.dispatch(Ff(r, i), { effects: a }), !0;
}
var $f = (e) => Qf(e, !1), ep = (e) => Qf(e, !0);
function tp(e, t, n) {
	let r = e.lineBlockAt(t.head), i = e.moveToLineBoundary(t, n);
	if (i.head == t.head && i.head != (n ? r.to : r.from) && (i = e.moveToLineBoundary(t, n, !1)), !n && i.head == r.from && r.length) {
		let n = /^\s*/.exec(e.state.sliceDoc(r.from, Math.min(r.from + 100, r.to)))[0].length;
		n && t.head != r.from + n && (i = D.cursor(r.from + n));
	}
	return i;
}
var np = (e) => If(e, (t) => tp(e, t, !0)), rp = (e) => If(e, (t) => tp(e, t, !1)), ip = (e) => If(e, (t) => tp(e, t, !Q(e))), ap = (e) => If(e, (t) => tp(e, t, Q(e))), op = (e) => If(e, (t) => D.cursor(e.lineBlockAt(t.head).from, 1)), sp = (e) => If(e, (t) => D.cursor(e.lineBlockAt(t.head).to, -1));
function cp(e, t, n) {
	let r = !1, i = Pf(e.selection, (t) => {
		let i = Ed(e, t.head, -1) || Ed(e, t.head, 1) || t.head > 0 && Ed(e, t.head - 1, 1) || t.head < e.doc.length && Ed(e, t.head + 1, -1);
		if (!i || !i.end) return t;
		r = !0;
		let a = i.start.from == t.head ? i.end.to : i.end.from;
		return n ? D.range(t.anchor, a) : D.cursor(a);
	});
	return r ? (t(Ff(e, i)), !0) : !1;
}
var lp = ({ state: e, dispatch: t }) => cp(e, t, !1);
function up(e, t, n) {
	let r = Pf(e.state.selection, (e) => {
		e.undirectional && e.head >= e.anchor != t && (e = D.range(e.head, e.anchor));
		let r = n(e);
		return D.range(e.anchor, r.head, r.goalColumn, r.bidiLevel || void 0, r.assoc);
	});
	return !r.eq(e.state.selection) && (e.dispatch(Ff(e.state, r)), !0);
}
function dp(e, t) {
	return up(e, t, (n) => e.moveByChar(n, t));
}
var fp = (e) => dp(e, !Q(e)), pp = (e) => dp(e, Q(e));
function mp(e, t) {
	return up(e, t, (n) => e.moveByGroup(n, t));
}
var hp = (e) => mp(e, !Q(e)), gp = (e) => mp(e, Q(e)), _p = (e) => {
	let t = !Q(e);
	return up(e, t, (n) => Gf(e.state, n, t));
}, vp = (e) => {
	let t = Q(e);
	return up(e, t, (n) => Gf(e.state, n, t));
};
function yp(e, t) {
	return up(e, t, (n) => e.moveVertically(n, t));
}
var bp = (e) => yp(e, !1), xp = (e) => yp(e, !0);
function Sp(e, t) {
	return up(e, t, (n) => e.moveVertically(n, t, Zf(e).height));
}
var Cp = (e) => Sp(e, !1), wp = (e) => Sp(e, !0), Tp = (e) => up(e, !0, (t) => tp(e, t, !0)), Ep = (e) => up(e, !1, (t) => tp(e, t, !1)), Dp = (e) => {
	let t = !Q(e);
	return up(e, t, (n) => tp(e, n, t));
}, Op = (e) => {
	let t = Q(e);
	return up(e, t, (n) => tp(e, n, t));
}, kp = (e) => up(e, !1, (t) => D.cursor(e.lineBlockAt(t.head).from)), Ap = (e) => up(e, !0, (t) => D.cursor(e.lineBlockAt(t.head).to)), jp = ({ state: e, dispatch: t }) => (t(Ff(e, { anchor: 0 })), !0), Mp = ({ state: e, dispatch: t }) => (t(Ff(e, { anchor: e.doc.length })), !0), Np = ({ state: e, dispatch: t }) => (t(Ff(e, {
	anchor: e.selection.main.anchor,
	head: 0
})), !0), Pp = ({ state: e, dispatch: t }) => (t(Ff(e, {
	anchor: e.selection.main.anchor,
	head: e.doc.length
})), !0), Fp = ({ state: e, dispatch: t }) => (t(e.update({
	selection: {
		anchor: 0,
		head: e.doc.length
	},
	userEvent: "select"
})), !0), Ip = ({ state: e, dispatch: t }) => {
	let n = tm(e).map(({ from: t, to: n }) => D.undirectionalRange(t, Math.min(n + 1, e.doc.length)));
	return t(e.update({
		selection: D.create(n),
		userEvent: "select"
	})), !0;
}, Lp = ({ state: e, dispatch: t }) => {
	let n = Pf(e.selection, (t) => {
		let n = Z(e), r = n.resolveStack(t.from, 1);
		if (t.empty) {
			let e = n.resolveStack(t.from, -1);
			e.node.from >= r.node.from && e.node.to <= r.node.to && (r = e);
		}
		for (let e = r; e; e = e.next) {
			let { node: n } = e;
			if ((n.from < t.from && n.to >= t.to || n.to > t.to && n.from <= t.from) && e.next) return D.undirectionalRange(n.from, n.to);
		}
		return t;
	});
	return !n.eq(e.selection) && (t(Ff(e, n)), !0);
};
function Rp(e, t) {
	let { state: n } = e, r = n.selection, i = n.selection.ranges.slice();
	for (let r of n.selection.ranges) {
		let a = n.doc.lineAt(r.head);
		if (t ? a.to < e.state.doc.length : a.from > 0) for (let n = r;;) {
			let r = e.moveVertically(n, t);
			if (r.head < a.from || r.head > a.to) {
				i.some((e) => e.head == r.head) || i.push(r);
				break;
			}
			if (r.head == n.head) break;
			n = r;
		}
	}
	return i.length != r.ranges.length && (e.dispatch(Ff(n, D.create(i, i.length - 1))), !0);
}
var zp = (e) => Rp(e, !1), Bp = (e) => Rp(e, !0), Vp = ({ state: e, dispatch: t }) => {
	let n = e.selection, r = null;
	return n.ranges.length > 1 ? r = D.create([n.main]) : n.main.empty || (r = D.create([D.cursor(n.main.head)])), r ? (t(Ff(e, r)), !0) : !1;
};
function Hp(e, t) {
	if (e.state.readOnly) return !1;
	let n = "delete.selection", { state: r } = e, i = r.changeByRange((r) => {
		let { from: i, to: a } = r;
		if (i == a) {
			let o = t(r);
			o < i ? (n = "delete.backward", o = Up(e, o, !1)) : o > i && (n = "delete.forward", o = Up(e, o, !0)), i = Math.min(i, o), a = Math.max(a, o);
		} else i = Up(e, i, !1), a = Up(e, a, !0);
		return i == a ? { range: r } : {
			changes: {
				from: i,
				to: a
			},
			range: D.cursor(i, i < r.head ? -1 : 1)
		};
	});
	return !i.changes.empty && (e.dispatch(r.update(i, {
		scrollIntoView: !0,
		userEvent: n,
		effects: n == "delete.selection" ? J.announce.of(r.phrase("Selection deleted")) : void 0
	})), !0);
}
function Up(e, t, n) {
	if (e instanceof J) for (let r of e.state.facet(J.atomicRanges).map((t) => t(e))) r.between(t, t, (e, r) => {
		e < t && r > t && (t = n ? r : e);
	});
	return t;
}
var Wp = (e, t, n) => Hp(e, (r) => {
	let i = r.from, { state: a } = e, o = a.doc.lineAt(i), s, c;
	if (n && !t && i > o.from && i < o.from + 200 && !/[^ \t]/.test(s = o.text.slice(0, i - o.from))) {
		if (s[s.length - 1] == "	") return i - 1;
		let e = Xt(s, a.tabSize) % hu(a) || hu(a);
		for (let t = 0; t < e && s[s.length - 1 - t] == " "; t++) i--;
		c = i;
	} else c = w(o.text, i - o.from, t, t) + o.from, c == i && o.number != (t ? a.doc.lines : 1) ? c += t ? 1 : -1 : !t && /[\ufe00-\ufe0f]/.test(o.text.slice(c - o.from, i - o.from)) && (c = w(o.text, c - o.from, !1, !1) + o.from);
	return c;
}), Gp = (e) => Wp(e, !1, !0), Kp = (e) => Wp(e, !0, !1), qp = (e, t) => Hp(e, (n) => {
	let r = n.head, { state: i } = e, a = i.doc.lineAt(r), o = i.charCategorizer(r);
	for (let e = null;;) {
		if (r == (t ? a.to : a.from)) {
			r == n.head && a.number != (t ? i.doc.lines : 1) && (r += t ? 1 : -1);
			break;
		}
		let s = w(a.text, r - a.from, t) + a.from, c = a.text.slice(Math.min(r, s) - a.from, Math.max(r, s) - a.from), l = o(c);
		if (e != null && l != e) break;
		(c != " " || r != n.head) && (e = l), r = s;
	}
	return r;
}), Jp = (e) => qp(e, !1), Yp = (e) => qp(e, !0), Xp = (e) => Hp(e, (t) => {
	let n = e.lineBlockAt(t.head).to;
	return t.head < n ? n : Math.min(e.state.doc.length, t.head + 1);
}), Zp = (e) => Hp(e, (t) => {
	let n = e.moveToLineBoundary(t, !1).head;
	return t.head > n ? n : Math.max(0, t.head - 1);
}), Qp = (e) => Hp(e, (t) => {
	let n = e.moveToLineBoundary(t, !0).head;
	return t.head < n ? n : Math.min(e.state.doc.length, t.head + 1);
}), $p = ({ state: e, dispatch: t }) => {
	if (e.readOnly) return !1;
	let n = e.changeByRange((e) => ({
		changes: {
			from: e.from,
			to: e.to,
			insert: C.of(["", ""])
		},
		range: D.cursor(e.from)
	}));
	return t(e.update(n, {
		scrollIntoView: !0,
		userEvent: "input"
	})), !0;
}, em = ({ state: e, dispatch: t }) => {
	if (e.readOnly) return !1;
	let n = e.changeByRange((t) => {
		if (!t.empty || t.from == 0 || t.from == e.doc.length) return { range: t };
		let n = t.from, r = e.doc.lineAt(n), i = n == r.from ? n - 1 : w(r.text, n - r.from, !1) + r.from, a = n == r.to ? n + 1 : w(r.text, n - r.from, !0) + r.from;
		return {
			changes: {
				from: i,
				to: a,
				insert: e.doc.slice(n, a).append(e.doc.slice(i, n))
			},
			range: D.cursor(a)
		};
	});
	return !n.changes.empty && (t(e.update(n, {
		scrollIntoView: !0,
		userEvent: "move.character"
	})), !0);
};
function tm(e) {
	let t = [], n = -1;
	for (let r of e.selection.ranges) {
		let i = e.doc.lineAt(r.from), a = e.doc.lineAt(r.to);
		if (!r.empty && r.to == a.from && (a = e.doc.lineAt(r.to - 1)), n >= i.number) {
			let e = t[t.length - 1];
			e.to = a.to, e.ranges.push(r);
		} else t.push({
			from: i.from,
			to: a.to,
			ranges: [r]
		});
		n = a.number + 1;
	}
	return t;
}
function nm(e, t, n) {
	if (e.readOnly) return !1;
	let r = [], i = [];
	for (let t of tm(e)) {
		if (n ? t.to == e.doc.length : t.from == 0) continue;
		let a = e.doc.lineAt(n ? t.to + 1 : t.from - 1), o = a.length + 1;
		if (n) {
			r.push({
				from: t.to,
				to: a.to
			}, {
				from: t.from,
				insert: a.text + e.lineBreak
			});
			for (let n of t.ranges) i.push(D.range(Math.min(e.doc.length, n.anchor + o), Math.min(e.doc.length, n.head + o)));
		} else {
			r.push({
				from: a.from,
				to: t.from
			}, {
				from: t.to,
				insert: e.lineBreak + a.text
			});
			for (let e of t.ranges) i.push(D.range(e.anchor - o, e.head - o));
		}
	}
	return r.length ? (t(e.update({
		changes: r,
		scrollIntoView: !0,
		selection: D.create(i, e.selection.mainIndex),
		userEvent: "move.line"
	})), !0) : !1;
}
var rm = ({ state: e, dispatch: t }) => nm(e, t, !1), im = ({ state: e, dispatch: t }) => nm(e, t, !0);
function am(e, t, n) {
	if (e.readOnly) return !1;
	let r = [];
	for (let t of tm(e)) n ? r.push({
		from: t.from,
		insert: e.doc.slice(t.from, t.to) + e.lineBreak
	}) : r.push({
		from: t.to,
		insert: e.lineBreak + e.doc.slice(t.from, t.to)
	});
	let i = e.changes(r);
	return t(e.update({
		changes: i,
		selection: e.selection.map(i, n ? 1 : -1),
		scrollIntoView: !0,
		userEvent: "input.copyline"
	})), !0;
}
var om = ({ state: e, dispatch: t }) => am(e, t, !1), sm = ({ state: e, dispatch: t }) => am(e, t, !0), cm = (e) => {
	if (e.state.readOnly) return !1;
	let { state: t } = e, n = t.changes(tm(t).map(({ from: e, to: n }) => (e > 0 ? e-- : n < t.doc.length && n++, {
		from: e,
		to: n
	}))), r = Pf(t.selection, (t) => {
		let n;
		if (e.lineWrapping) {
			let r = e.lineBlockAt(t.head), i = e.coordsAtPos(t.head, t.assoc || 1);
			i && (n = r.bottom + e.documentTop - i.bottom + e.defaultLineHeight / 2);
		}
		return e.moveVertically(t, !0, n);
	}).map(n);
	return e.dispatch({
		changes: n,
		selection: r,
		scrollIntoView: !0,
		userEvent: "delete.line"
	}), !0;
};
function lm(e, t) {
	if (/\(\)|\[\]|\{\}/.test(e.sliceDoc(t - 1, t + 1))) return {
		from: t,
		to: t
	};
	let r = Z(e).resolveInner(t), i = r.childBefore(t), a = r.childAfter(t), o;
	return i && a && i.to <= t && a.from >= t && (o = i.type.prop(n.closedBy)) && o.indexOf(a.name) > -1 && e.doc.lineAt(i.to).from == e.doc.lineAt(a.from).from && !/\S/.test(e.sliceDoc(i.to, a.from)) ? {
		from: i.to,
		to: a.from
	} : null;
}
var um = /*@__PURE__*/ fm(!1), dm = /*@__PURE__*/ fm(!0);
function fm(e) {
	return ({ state: t, dispatch: n }) => {
		if (t.readOnly) return !1;
		let r = t.changeByRange((n) => {
			let { from: r, to: i } = n, a = t.doc.lineAt(r), o = !e && r == i && lm(t, r);
			e && (r = i = (i <= a.to ? a : t.doc.lineAt(i)).to);
			let s = new vu(t, {
				simulateBreak: r,
				simulateDoubleBreak: !!o
			}), c = _u(s, r);
			for (c == null && (c = Xt(/^\s*/.exec(t.doc.lineAt(r).text)[0], t.tabSize)); i < a.to && /\s/.test(a.text[i - a.from]);) i++;
			o ? {from: r, to: i} = o : r > a.from && r < a.from + 100 && !/\S/.test(a.text.slice(0, r)) && (r = a.from);
			let l = ["", gu(t, c)];
			return o && l.push(gu(t, s.lineIndent(a.from, -1))), {
				changes: {
					from: r,
					to: i,
					insert: C.of(l)
				},
				range: D.cursor(r + 1 + l[1].length)
			};
		});
		return n(t.update(r, {
			scrollIntoView: !0,
			userEvent: "input"
		})), !0;
	};
}
function pm(e, t) {
	let n = -1;
	return e.changeByRange((r) => {
		let i = [];
		for (let a = r.from; a <= r.to;) {
			let o = e.doc.lineAt(a);
			o.number > n && (r.empty || r.to > o.from) && (t(o, i, r), n = o.number), a = o.to + 1;
		}
		let a = e.changes(i);
		return {
			changes: i,
			range: D.range(a.mapPos(r.anchor, 1), a.mapPos(r.head, 1))
		};
	});
}
var mm = ({ state: e, dispatch: t }) => {
	if (e.readOnly) return !1;
	let n = Object.create(null), r = new vu(e, { overrideIndentation: (e) => {
		let t = n[e];
		return t == null ? -1 : t;
	} }), i = pm(e, (t, i, a) => {
		let o = _u(r, t.from);
		if (o == null) return;
		/\S/.test(t.text) || (o = 0);
		let s = /^\s*/.exec(t.text)[0], c = gu(e, o);
		(s != c || a.from < t.from + s.length) && (n[t.from] = o, i.push({
			from: t.from,
			to: t.from + s.length,
			insert: c
		}));
	});
	return i.changes.empty || t(e.update(i, { userEvent: "indent" })), !0;
}, hm = ({ state: e, dispatch: t }) => !e.readOnly && (t(e.update(pm(e, (t, n) => {
	n.push({
		from: t.from,
		insert: e.facet(mu)
	});
}), { userEvent: "input.indent" })), !0), gm = ({ state: e, dispatch: t }) => !e.readOnly && (t(e.update(pm(e, (t, n) => {
	let r = /^\s*/.exec(t.text)[0];
	if (!r) return;
	let i = Xt(r, e.tabSize), a = 0, o = gu(e, Math.max(0, i - hu(e)));
	for (; a < r.length && a < o.length && r.charCodeAt(a) == o.charCodeAt(a);) a++;
	n.push({
		from: t.from + a,
		to: t.from + r.length,
		insert: o.slice(a)
	});
}), { userEvent: "delete.dedent" })), !0), _m = (e) => (e.setTabFocusMode(), !0), vm = [
	{
		key: "Ctrl-b",
		run: zf,
		shift: fp,
		preventDefault: !0
	},
	{
		key: "Ctrl-f",
		run: Bf,
		shift: pp
	},
	{
		key: "Ctrl-p",
		run: Yf,
		shift: bp
	},
	{
		key: "Ctrl-n",
		run: Xf,
		shift: xp
	},
	{
		key: "Ctrl-a",
		run: op,
		shift: kp
	},
	{
		key: "Ctrl-e",
		run: sp,
		shift: Ap
	},
	{
		key: "Ctrl-d",
		run: Kp
	},
	{
		key: "Ctrl-h",
		run: Gp
	},
	{
		key: "Ctrl-k",
		run: Xp
	},
	{
		key: "Ctrl-Alt-h",
		run: Jp
	},
	{
		key: "Ctrl-o",
		run: $p
	},
	{
		key: "Ctrl-t",
		run: em
	},
	{
		key: "Ctrl-v",
		run: ep
	}
], ym = /*@__PURE__*/ [
	{
		key: "ArrowLeft",
		run: zf,
		shift: fp,
		preventDefault: !0
	},
	{
		key: "Mod-ArrowLeft",
		mac: "Alt-ArrowLeft",
		run: Hf,
		shift: hp,
		preventDefault: !0
	},
	{
		mac: "Cmd-ArrowLeft",
		run: ip,
		shift: Dp,
		preventDefault: !0
	},
	{
		key: "ArrowRight",
		run: Bf,
		shift: pp,
		preventDefault: !0
	},
	{
		key: "Mod-ArrowRight",
		mac: "Alt-ArrowRight",
		run: Uf,
		shift: gp,
		preventDefault: !0
	},
	{
		mac: "Cmd-ArrowRight",
		run: ap,
		shift: Op,
		preventDefault: !0
	},
	{
		key: "ArrowUp",
		run: Yf,
		shift: bp,
		preventDefault: !0
	},
	{
		mac: "Cmd-ArrowUp",
		run: jp,
		shift: Np
	},
	{
		mac: "Ctrl-ArrowUp",
		run: $f,
		shift: Cp
	},
	{
		key: "ArrowDown",
		run: Xf,
		shift: xp,
		preventDefault: !0
	},
	{
		mac: "Cmd-ArrowDown",
		run: Mp,
		shift: Pp
	},
	{
		mac: "Ctrl-ArrowDown",
		run: ep,
		shift: wp
	},
	{
		key: "PageUp",
		run: $f,
		shift: Cp
	},
	{
		key: "PageDown",
		run: ep,
		shift: wp
	},
	{
		key: "Home",
		run: rp,
		shift: Ep,
		preventDefault: !0
	},
	{
		key: "Mod-Home",
		run: jp,
		shift: Np
	},
	{
		key: "End",
		run: np,
		shift: Tp,
		preventDefault: !0
	},
	{
		key: "Mod-End",
		run: Mp,
		shift: Pp
	},
	{
		key: "Enter",
		run: um,
		shift: um
	},
	{
		key: "Mod-a",
		run: Fp
	},
	{
		key: "Backspace",
		run: Gp,
		shift: Gp,
		preventDefault: !0
	},
	{
		key: "Delete",
		run: Kp,
		preventDefault: !0
	},
	{
		key: "Mod-Backspace",
		mac: "Alt-Backspace",
		run: Jp,
		preventDefault: !0
	},
	{
		key: "Mod-Delete",
		mac: "Alt-Delete",
		run: Yp,
		preventDefault: !0
	},
	{
		mac: "Mod-Backspace",
		run: Zp,
		preventDefault: !0
	},
	{
		mac: "Mod-Delete",
		run: Qp,
		preventDefault: !0
	}
].concat(/*@__PURE__*/ vm.map((e) => ({
	mac: e.key,
	run: e.run,
	shift: e.shift
}))), bm = /*@__PURE__*/ [
	{
		key: "Alt-ArrowLeft",
		mac: "Ctrl-ArrowLeft",
		run: Kf,
		shift: _p
	},
	{
		key: "Alt-ArrowRight",
		mac: "Ctrl-ArrowRight",
		run: qf,
		shift: vp
	},
	{
		key: "Alt-ArrowUp",
		run: rm
	},
	{
		key: "Shift-Alt-ArrowUp",
		run: om
	},
	{
		key: "Alt-ArrowDown",
		run: im
	},
	{
		key: "Shift-Alt-ArrowDown",
		run: sm
	},
	{
		key: "Mod-Alt-ArrowUp",
		run: zp
	},
	{
		key: "Mod-Alt-ArrowDown",
		run: Bp
	},
	{
		key: "Escape",
		run: Vp
	},
	{
		key: "Mod-Enter",
		run: dm
	},
	{
		key: "Alt-l",
		mac: "Ctrl-l",
		run: Ip
	},
	{
		key: "Mod-i",
		run: Lp,
		preventDefault: !0
	},
	{
		key: "Mod-[",
		run: gm
	},
	{
		key: "Mod-]",
		run: hm
	},
	{
		key: "Mod-Alt-\\",
		run: mm
	},
	{
		key: "Shift-Mod-k",
		run: cm
	},
	{
		key: "Shift-Mod-\\",
		run: lp
	},
	{
		key: "Mod-/",
		run: Zd
	},
	{
		key: "Alt-A",
		mac: "Ctrl-A",
		run: ef
	},
	{
		key: "Ctrl-m",
		mac: "Shift-Alt-m",
		run: _m
	}
].concat(ym), xm = typeof String.prototype.normalize == "function" ? (e) => e.normalize("NFKD") : (e) => e, Sm = class {
	constructor(e, t, n = 0, r = e.length, i, a) {
		this.test = a, this.value = {
			from: 0,
			to: 0,
			precise: !1
		}, this.done = !1, this.matches = [], this.buffer = "", this.bufferPos = 0, this.iter = e.iterRange(n, r), this.bufferStart = n, this.normalize = i ? (e) => i(xm(e)) : xm, this.query = this.normalize(t);
	}
	peek() {
		if (this.bufferPos == this.buffer.length) {
			if (this.bufferStart += this.buffer.length, this.iter.next(), this.iter.done) return -1;
			this.bufferPos = 0, this.buffer = this.iter.value;
		}
		return Pe(this.buffer, this.bufferPos);
	}
	next() {
		for (; this.matches.length;) this.matches.pop();
		return this.nextOverlapping();
	}
	nextOverlapping() {
		for (;;) {
			let e = this.peek();
			if (e < 0) return this.done = !0, this;
			let t = Fe(e), n = this.bufferStart + this.bufferPos;
			this.bufferPos += Ie(e);
			let r = this.normalize(t);
			if (r.length) for (let e = 0, i = n, a = !0;; e++) {
				let n = r.charCodeAt(e), o = this.match(n, i, a, this.bufferPos + this.bufferStart, e == r.length - 1);
				if (o) return this.value = o, this;
				if (e == r.length - 1) break;
				a && e < t.length && t.charCodeAt(e) == n ? i++ : a = !1;
			}
		}
	}
	match(e, t, n, r, i) {
		let a = null;
		for (let t = 0; t < this.matches.length;) {
			let n = this.matches[t], o = !1;
			this.query.charCodeAt(n.index) == e && (n.index == this.query.length - 1 ? a = {
				from: n.from,
				to: r,
				precise: i && n.precise
			} : (n.index++, o = !0)), o ? t++ : this.matches.splice(t, 1);
		}
		return this.query.charCodeAt(0) == e && (this.query.length == 1 ? a = {
			from: t,
			to: r,
			precise: n && i
		} : this.matches.push({
			from: t,
			index: 1,
			precise: n
		})), a && this.test && !this.test(a.from, a.to, this.buffer, this.bufferStart) && (a = null), a;
	}
};
typeof Symbol < "u" && (Sm.prototype[Symbol.iterator] = function() {
	return this;
});
var Cm = {
	from: -1,
	to: -1,
	match: /*@__PURE__*/ /.*/.exec(""),
	precise: !0
}, wm = "gm" + (/x/.unicode == null ? "" : "u"), Tm = class {
	constructor(e, t, n, r = 0, i = e.length) {
		if (this.text = e, this.to = i, this.curLine = "", this.done = !1, this.value = Cm, /\\[sWDnr]|\n|\r|\[\^/.test(t)) return new Om(e, t, n, r, i);
		this.re = new RegExp(t, wm + (n != null && n.ignoreCase ? "i" : "")), this.test = n == null ? void 0 : n.test, this.iter = e.iter();
		let a = e.lineAt(r);
		this.curLineStart = a.from, this.matchPos = Am(e, r), this.getLine(this.curLineStart);
	}
	getLine(e) {
		this.iter.next(e), this.iter.lineBreak ? this.curLine = "" : (this.curLine = this.iter.value, this.curLineStart + this.curLine.length > this.to && (this.curLine = this.curLine.slice(0, this.to - this.curLineStart)), this.iter.next());
	}
	nextLine() {
		this.curLineStart = this.curLineStart + this.curLine.length + 1, this.curLineStart > this.to ? this.curLine = "" : this.getLine(0);
	}
	next() {
		for (let e = this.matchPos - this.curLineStart;;) {
			this.re.lastIndex = e;
			let t = this.matchPos <= this.to && this.re.exec(this.curLine);
			if (t) {
				let n = this.curLineStart + t.index, r = n + t[0].length;
				if (this.matchPos = Am(this.text, r + +(n == r)), n == this.curLineStart + this.curLine.length && this.nextLine(), (n < r || n > this.value.to) && (!this.test || this.test(n, r, t))) return this.value = {
					from: n,
					to: r,
					precise: !0,
					match: t
				}, this;
				e = this.matchPos - this.curLineStart;
			} else if (this.curLineStart + this.curLine.length < this.to) this.nextLine(), e = 0;
			else return this.done = !0, this;
		}
	}
}, Em = /*@__PURE__*/ new WeakMap(), Dm = class e {
	constructor(e, t) {
		this.from = e, this.text = t;
	}
	get to() {
		return this.from + this.text.length;
	}
	static get(t, n, r) {
		let i = Em.get(t);
		if (!i || i.from >= r || i.to <= n) {
			let i = new e(n, t.sliceString(n, r));
			return Em.set(t, i), i;
		}
		if (i.from == n && i.to == r) return i;
		let { text: a, from: o } = i;
		return o > n && (a = t.sliceString(n, o) + a, o = n), i.to < r && (a += t.sliceString(i.to, r)), Em.set(t, new e(o, a)), new e(n, a.slice(n - o, r - o));
	}
}, Om = class {
	constructor(e, t, n, r, i) {
		this.text = e, this.to = i, this.done = !1, this.value = Cm, this.matchPos = Am(e, r), this.re = new RegExp(t, wm + (n != null && n.ignoreCase ? "i" : "")), this.test = n == null ? void 0 : n.test, this.flat = Dm.get(e, r, this.chunkEnd(r + 5e3));
	}
	chunkEnd(e) {
		return e >= this.to ? this.to : this.text.lineAt(e).to;
	}
	next() {
		for (;;) {
			let e = this.re.lastIndex = this.matchPos - this.flat.from, t = this.re.exec(this.flat.text);
			if (t && !t[0] && t.index == e && (this.re.lastIndex = e + 1, t = this.re.exec(this.flat.text)), t) {
				let e = this.flat.from + t.index, n = e + t[0].length;
				if ((this.flat.to >= this.to || t.index + t[0].length <= this.flat.text.length - 10) && (!this.test || this.test(e, n, t))) return this.value = {
					from: e,
					to: n,
					precise: !0,
					match: t
				}, this.matchPos = Am(this.text, n + +(e == n)), this;
			}
			if (this.flat.to == this.to) return this.done = !0, this;
			this.flat = Dm.get(this.text, this.flat.from, this.chunkEnd(this.flat.from + this.flat.text.length * 2));
		}
	}
};
typeof Symbol < "u" && (Tm.prototype[Symbol.iterator] = Om.prototype[Symbol.iterator] = function() {
	return this;
});
function km(e) {
	try {
		return new RegExp(e, wm), !0;
	} catch (e) {
		return !1;
	}
}
function Am(e, t) {
	if (t >= e.length) return t;
	let n = e.lineAt(t), r;
	for (; t < n.to && (r = n.text.charCodeAt(t - n.from)) >= 56320 && r < 57344;) t++;
	return t;
}
var jm = (e) => {
	let { state: t } = e, n = String(t.doc.lineAt(e.state.selection.main.head).number), { close: r, result: i } = qc(e, {
		label: t.phrase("Go to line"),
		input: {
			type: "text",
			name: "line",
			value: n
		},
		focus: !0,
		submitLabel: t.phrase("go")
	});
	return i.then((n) => {
		let i = n && /^([+-])?(\d+)?(:\d+)?(%)?$/.exec(n.elements.line.value);
		if (!i) {
			e.dispatch({ effects: r });
			return;
		}
		let a = t.doc.lineAt(t.selection.main.head), [, o, s, c, l] = i, u = c ? +c.slice(1) : 0, d = s ? +s : a.number;
		if (s && l) {
			let e = d / 100;
			o && (e = e * (o == "-" ? -1 : 1) + a.number / t.doc.lines), d = Math.round(t.doc.lines * e);
		} else s && o && (d = d * (o == "-" ? -1 : 1) + a.number);
		let f = t.doc.line(Math.max(1, Math.min(t.doc.lines, d))), p = D.cursor(f.from + Math.max(0, Math.min(u, f.length)));
		e.dispatch({
			effects: [r, J.scrollIntoView(p.from, { y: "center" })],
			selection: p
		});
	}), !0;
}, Mm = {
	highlightWordAroundCursor: !1,
	minSelectionLength: 1,
	maxMatches: 100,
	wholeWords: !1
}, Nm = /*@__PURE__*/ O.define({ combine(e) {
	return Mt(e, Mm, {
		highlightWordAroundCursor: (e, t) => e || t,
		minSelectionLength: Math.min,
		maxMatches: Math.min
	});
} });
function Pm(e) {
	let t = [Bm, zm];
	return e && t.push(Nm.of(e)), t;
}
var Fm = /*@__PURE__*/ B.mark({ class: "cm-selectionMatch" }), Im = /*@__PURE__*/ B.mark({ class: "cm-selectionMatch cm-selectionMatch-main" });
function Lm(e, t, n, r) {
	return (n == 0 || e(t.sliceDoc(n - 1, n)) != M.Word) && (r == t.doc.length || e(t.sliceDoc(r, r + 1)) != M.Word);
}
function Rm(e, t, n, r) {
	return e(t.sliceDoc(n, n + 1)) == M.Word && e(t.sliceDoc(r - 1, r)) == M.Word;
}
var zm = /*@__PURE__*/ W.fromClass(class {
	constructor(e) {
		this.decorations = this.getDeco(e);
	}
	update(e) {
		(e.selectionSet || e.docChanged || e.viewportChanged) && (this.decorations = this.getDeco(e.view));
	}
	getDeco(e) {
		let t = e.state.facet(Nm), { state: n } = e, r = n.selection;
		if (r.ranges.length > 1) return B.none;
		let i = r.main, a, o = null;
		if (i.empty) {
			if (!t.highlightWordAroundCursor) return B.none;
			let e = n.wordAt(i.head);
			if (!e) return B.none;
			o = n.charCategorizer(i.head), a = n.sliceDoc(e.from, e.to);
		} else {
			let e = i.to - i.from;
			if (e < t.minSelectionLength || e > 200) return B.none;
			if (t.wholeWords) {
				if (a = n.sliceDoc(i.from, i.to), o = n.charCategorizer(i.head), !(Lm(o, n, i.from, i.to) && Rm(o, n, i.from, i.to))) return B.none;
			} else if (a = n.sliceDoc(i.from, i.to), !a) return B.none;
		}
		let s = [];
		for (let r of e.visibleRanges) {
			let e = new Sm(n.doc, a, r.from, r.to);
			for (; !e.next().done;) {
				let { from: r, to: a } = e.value;
				if ((!o || Lm(o, n, r, a)) && (i.empty && r <= i.from && a >= i.to ? s.push(Im.range(r, a)) : (r >= i.to || a <= i.from) && s.push(Fm.range(r, a)), s.length > t.maxMatches)) return B.none;
			}
		}
		return B.set(s);
	}
}, { decorations: (e) => e.decorations }), Bm = /*@__PURE__*/ J.baseTheme({
	".cm-selectionMatch": { backgroundColor: "#99ff7780" },
	".cm-searchMatch .cm-selectionMatch": { backgroundColor: "transparent" }
}), Vm = ({ state: e, dispatch: t }) => {
	let { selection: n } = e, r = D.create(n.ranges.map((t) => e.wordAt(t.head) || D.cursor(t.head)), n.mainIndex);
	return !r.eq(n) && (t(e.update({ selection: r })), !0);
};
function Hm(e, t) {
	let { main: n, ranges: r } = e.selection, i = e.wordAt(n.head), a = i && i.from == n.from && i.to == n.to;
	for (let n = !1, i = new Sm(e.doc, t, r[r.length - 1].to);;) if (i.next(), i.done) {
		if (n) return null;
		i = new Sm(e.doc, t, 0, Math.max(0, r[r.length - 1].from - 1)), n = !0;
	} else {
		if (n && r.some((e) => e.from == i.value.from)) continue;
		if (a) {
			let t = e.wordAt(i.value.from);
			if (!t || t.from != i.value.from || t.to != i.value.to) continue;
		}
		return i.value;
	}
}
var Um = ({ state: e, dispatch: t }) => {
	let { ranges: n } = e.selection;
	if (n.some((e) => e.from === e.to)) return Vm({
		state: e,
		dispatch: t
	});
	let r = e.sliceDoc(n[0].from, n[0].to);
	if (e.selection.ranges.some((t) => e.sliceDoc(t.from, t.to) != r)) return !1;
	let i = Hm(e, r);
	return i ? (t(e.update({
		selection: e.selection.addRange(D.range(i.from, i.to), !1),
		effects: J.scrollIntoView(i.to)
	})), !0) : !1;
}, Wm = /*@__PURE__*/ O.define({ combine(e) {
	return Mt(e, {
		top: !1,
		caseSensitive: !1,
		literal: !1,
		regexp: !1,
		wholeWord: !1,
		createPanel: (e) => new wh(e),
		scrollToMatch: (e) => J.scrollIntoView(e)
	});
} }), Gm = class {
	constructor(e) {
		this.search = e.search, this.caseSensitive = !!e.caseSensitive, this.literal = !!e.literal, this.regexp = !!e.regexp, this.replace = e.replace || "", this.valid = !!this.search && (!this.regexp || km(this.search)), this.unquoted = this.unquote(this.search), this.wholeWord = !!e.wholeWord, this.test = e.test;
	}
	unquote(e) {
		return this.literal ? e : e.replace(/\\([nrt\\])/g, (e, t) => t == "n" ? "\n" : t == "r" ? "\r" : t == "t" ? "	" : "\\");
	}
	eq(e) {
		return this.search == e.search && this.replace == e.replace && this.caseSensitive == e.caseSensitive && this.regexp == e.regexp && this.wholeWord == e.wholeWord && this.test == e.test;
	}
	create() {
		return this.regexp ? new nh(this) : new Xm(this);
	}
	getCursor(e, t = 0, n) {
		let r = e.doc ? e : N.create({ doc: e });
		return n == null && (n = r.doc.length), this.regexp ? Qm(this, r, t, n) : Jm(this, r, t, n);
	}
}, Km = class {
	constructor(e) {
		this.spec = e;
	}
};
function qm(e, t, n) {
	return (r, i, a, o) => n && !n(r, i, a, o) ? !1 : e(r >= o && i <= o + a.length ? a.slice(r - o, i - o) : t.doc.sliceString(r, i), t, r, i);
}
function Jm(e, t, n, r) {
	let i;
	return e.wholeWord && (i = Ym(t.doc, t.charCategorizer(t.selection.main.head))), e.test && (i = qm(e.test, t, i)), new Sm(t.doc, e.unquoted, n, r, e.caseSensitive ? void 0 : (e) => e.toLowerCase(), i);
}
function Ym(e, t) {
	return (n, r, i, a) => ((a > n || a + i.length < r) && (a = Math.max(0, n - 2), i = e.sliceString(a, Math.min(e.length, r + 2))), (t($m(i, n - a)) != M.Word || t(eh(i, n - a)) != M.Word) && (t(eh(i, r - a)) != M.Word || t($m(i, r - a)) != M.Word));
}
var Xm = class extends Km {
	constructor(e) {
		super(e);
	}
	nextMatch(e, t, n) {
		let r = Jm(this.spec, e, n, e.doc.length).nextOverlapping();
		if (r.done) {
			let n = Math.min(e.doc.length, t + this.spec.unquoted.length);
			r = Jm(this.spec, e, 0, n).nextOverlapping();
		}
		return r.done || r.value.from == t && r.value.to == n ? null : r.value;
	}
	prevMatchInRange(e, t, n) {
		for (let r = n;;) {
			let n = Math.max(t, r - 1e4 - this.spec.unquoted.length), i = Jm(this.spec, e, n, r), a = null;
			for (; !i.nextOverlapping().done;) a = i.value;
			if (a) return a;
			if (n == t) return null;
			r -= 1e4;
		}
	}
	prevMatch(e, t, n) {
		let r = this.prevMatchInRange(e, 0, t);
		return r || (r = this.prevMatchInRange(e, Math.max(0, n - this.spec.unquoted.length), e.doc.length)), r && (r.from != t || r.to != n) ? r : null;
	}
	getReplacement(e) {
		return this.spec.unquote(this.spec.replace);
	}
	matchAll(e, t) {
		let n = Jm(this.spec, e, 0, e.doc.length), r = [];
		for (; !n.next().done;) {
			if (r.length >= t) return null;
			r.push(n.value);
		}
		return r;
	}
	highlight(e, t, n, r) {
		let i = Jm(this.spec, e, Math.max(0, t - this.spec.unquoted.length), Math.min(n + this.spec.unquoted.length, e.doc.length));
		for (; !i.next().done;) r(i.value.from, i.value.to);
	}
};
function Zm(e, t, n) {
	return (r, i, a) => (!n || n(r, i, a)) && e(a[0], t, r, i);
}
function Qm(e, t, n, r) {
	let i;
	return e.wholeWord && (i = th(t.charCategorizer(t.selection.main.head))), e.test && (i = Zm(e.test, t, i)), new Tm(t.doc, e.search, {
		ignoreCase: !e.caseSensitive,
		test: i
	}, n, r);
}
function $m(e, t) {
	return e.slice(w(e, t, !1), t);
}
function eh(e, t) {
	return e.slice(t, w(e, t));
}
function th(e) {
	return (t, n, r) => !r[0].length || (e($m(r.input, r.index)) != M.Word || e(eh(r.input, r.index)) != M.Word) && (e(eh(r.input, r.index + r[0].length)) != M.Word || e($m(r.input, r.index + r[0].length)) != M.Word);
}
var nh = class extends Km {
	nextMatch(e, t, n) {
		let r = Qm(this.spec, e, n, e.doc.length).next();
		return r.done && (r = Qm(this.spec, e, 0, t).next()), r.done ? null : r.value;
	}
	prevMatchInRange(e, t, n) {
		for (let r = 1;; r++) {
			let i = Math.max(t, n - r * 1e4), a = Qm(this.spec, e, i, n), o = null;
			for (; !a.next().done;) o = a.value;
			if (o && (i == t || o.from > i + 10)) return o;
			if (i == t) return null;
		}
	}
	prevMatch(e, t, n) {
		return this.prevMatchInRange(e, 0, t) || this.prevMatchInRange(e, n, e.doc.length);
	}
	getReplacement(e) {
		return this.spec.unquote(this.spec.replace).replace(/\$([$&]|\d+)/g, (t, n) => {
			if (n == "&") return e.match[0];
			if (n == "$") return "$";
			for (let t = n.length; t > 0; t--) {
				let r = +n.slice(0, t);
				if (r > 0 && r < e.match.length) return e.match[r] + n.slice(t);
			}
			return t;
		});
	}
	matchAll(e, t) {
		let n = Qm(this.spec, e, 0, e.doc.length), r = [];
		for (; !n.next().done;) {
			if (r.length >= t) return null;
			r.push(n.value);
		}
		return r;
	}
	highlight(e, t, n, r) {
		let i = Qm(this.spec, e, Math.max(0, t - 250), Math.min(n + 250, e.doc.length));
		for (; !i.next().done;) r(i.value.from, i.value.to);
	}
}, rh = /*@__PURE__*/ A.define(), ih = /*@__PURE__*/ A.define(), ah = /*@__PURE__*/ k.define({
	create(e) {
		return new oh(vh(e).create(), null);
	},
	update(e, t) {
		for (let n of t.effects) n.is(rh) ? e = new oh(n.value.create(), e.panel) : n.is(ih) && (e = new oh(e.query, n.value ? _h : null));
		return e;
	},
	provide: (e) => Kc.from(e, (e) => e.panel)
}), oh = class {
	constructor(e, t) {
		this.query = e, this.panel = t;
	}
}, sh = /*@__PURE__*/ B.mark({ class: "cm-searchMatch" }), ch = /*@__PURE__*/ B.mark({ class: "cm-searchMatch cm-searchMatch-selected" }), lh = /*@__PURE__*/ W.fromClass(class {
	constructor(e) {
		this.view = e, this.decorations = this.highlight(e.state.field(ah));
	}
	update(e) {
		let t = e.state.field(ah);
		(t != e.startState.field(ah) || e.docChanged || e.selectionSet || e.viewportChanged) && (this.decorations = this.highlight(t));
	}
	highlight({ query: e, panel: t }) {
		if (!t || !e.spec.valid) return B.none;
		let { view: n } = this, r = new zt();
		for (let t = 0, i = n.visibleRanges, a = i.length; t < a; t++) {
			let { from: o, to: s } = i[t];
			for (; t < a - 1 && s > i[t + 1].from - 500;) s = i[++t].to;
			e.highlight(n.state, o, s, (e, t) => {
				let i = n.state.selection.ranges.some((n) => n.from == e && n.to == t);
				r.add(e, t, i ? ch : sh);
			});
		}
		return r.finish();
	}
}, { decorations: (e) => e.decorations });
function uh(e) {
	return (t) => {
		let n = t.state.field(ah, !1);
		return n && n.query.spec.valid ? e(t, n) : xh(t);
	};
}
var dh = /*@__PURE__*/ uh((e, { query: t }) => {
	let { to: n } = e.state.selection.main, r = t.nextMatch(e.state, n, n);
	if (!r) return !1;
	let i = D.single(r.from, r.to), a = e.state.facet(Wm);
	return e.dispatch({
		selection: i,
		effects: [Oh(e, r), a.scrollToMatch(i.main, e)],
		userEvent: "select.search"
	}), bh(e), !0;
}), fh = /*@__PURE__*/ uh((e, { query: t }) => {
	let { state: n } = e, { from: r } = n.selection.main, i = t.prevMatch(n, r, r);
	if (!i) return !1;
	let a = D.single(i.from, i.to), o = e.state.facet(Wm);
	return e.dispatch({
		selection: a,
		effects: [Oh(e, i), o.scrollToMatch(a.main, e)],
		userEvent: "select.search"
	}), bh(e), !0;
}), ph = /*@__PURE__*/ uh((e, { query: t }) => {
	let n = t.matchAll(e.state, 1e3);
	return !n || !n.length ? !1 : (e.dispatch({
		selection: D.create(n.map((e) => D.range(e.from, e.to))),
		userEvent: "select.search.matches"
	}), !0);
}), mh = ({ state: e, dispatch: t }) => {
	let n = e.selection;
	if (n.ranges.length > 1 || n.main.empty) return !1;
	let { from: r, to: i } = n.main, a = [], o = 0;
	for (let t = new Sm(e.doc, e.sliceDoc(r, i)); !t.next().done;) {
		if (a.length > 1e3) return !1;
		t.value.from == r && (o = a.length), a.push(D.range(t.value.from, t.value.to));
	}
	return t(e.update({
		selection: D.create(a, o),
		userEvent: "select.search.matches"
	})), !0;
}, hh = /*@__PURE__*/ uh((e, { query: t }) => {
	let { state: n } = e, { from: r, to: i } = n.selection.main;
	if (n.readOnly) return !1;
	let a = t.nextMatch(n, r, r);
	if (!a) return !1;
	let o = a, s = [], c, l, u = [];
	o.precise ? o.from == r && o.to == i && (l = n.toText(t.getReplacement(o)), s.push({
		from: o.from,
		to: o.to,
		insert: l
	}), o = t.nextMatch(n, o.from, o.to), u.push(J.announce.of(n.phrase("replaced match on line $", n.doc.lineAt(r).number) + "."))) : o = t.nextMatch(n, o.from, o.to);
	let d = e.state.changes(s);
	return o && (c = D.single(o.from, o.to).map(d), u.push(Oh(e, o)), u.push(n.facet(Wm).scrollToMatch(c.main, e))), e.dispatch({
		changes: d,
		selection: c,
		effects: u,
		userEvent: "input.replace"
	}), !0;
}), gh = /*@__PURE__*/ uh((e, { query: t }) => {
	if (e.state.readOnly) return !1;
	let n = [];
	for (let r of t.matchAll(e.state, 1e9)) {
		let { from: e, to: i, precise: a } = r;
		a && n.push({
			from: e,
			to: i,
			insert: t.getReplacement(r)
		});
	}
	if (!n.length) return !1;
	let r = e.state.phrase("replaced $ matches", n.length) + ".";
	return e.dispatch({
		changes: n,
		effects: J.announce.of(r),
		userEvent: "input.replace.all"
	}), !0;
});
function _h(e) {
	return e.state.facet(Wm).createPanel(e);
}
function vh(e, t) {
	var n, r, i, a, o;
	let s = e.selection.main, c = s.empty || s.to > s.from + 100 ? "" : e.sliceDoc(s.from, s.to);
	if (t && !c) return t;
	let l = e.facet(Wm);
	return new Gm({
		search: ((n = t == null ? void 0 : t.literal) == null ? l.literal : n) ? c : c.replace(/\n/g, "\\n"),
		caseSensitive: (r = t == null ? void 0 : t.caseSensitive) == null ? l.caseSensitive : r,
		literal: (i = t == null ? void 0 : t.literal) == null ? l.literal : i,
		regexp: (a = t == null ? void 0 : t.regexp) == null ? l.regexp : a,
		wholeWord: (o = t == null ? void 0 : t.wholeWord) == null ? l.wholeWord : o
	});
}
function yh(e) {
	let t = Hc(e, _h);
	return t && t.dom.querySelector("[main-field]");
}
function bh(e) {
	let t = yh(e);
	t && t == e.root.activeElement && t.select();
}
var xh = (e) => {
	let t = e.state.field(ah, !1);
	if (t && t.panel) {
		let n = yh(e);
		if (n && n != e.root.activeElement) {
			let r = vh(e.state, t.query.spec);
			r.valid && e.dispatch({ effects: rh.of(r) }), n.focus(), n.select();
		}
	} else e.dispatch({ effects: [ih.of(!0), t ? rh.of(vh(e.state, t.query.spec)) : A.appendConfig.of(Ah)] });
	return !0;
}, Sh = (e) => {
	let t = e.state.field(ah, !1);
	if (!t || !t.panel) return !1;
	let n = Hc(e, _h);
	return n && n.dom.contains(e.root.activeElement) && e.focus(), e.dispatch({ effects: ih.of(!1) }), !0;
}, Ch = [
	{
		key: "Mod-f",
		run: xh,
		scope: "editor search-panel"
	},
	{
		key: "F3",
		run: dh,
		shift: fh,
		scope: "editor search-panel",
		preventDefault: !0
	},
	{
		key: "Mod-g",
		run: dh,
		shift: fh,
		scope: "editor search-panel",
		preventDefault: !0
	},
	{
		key: "Escape",
		run: Sh,
		scope: "editor search-panel"
	},
	{
		key: "Mod-Shift-l",
		run: mh
	},
	{
		key: "Mod-Alt-g",
		run: jm
	},
	{
		key: "Mod-d",
		run: Um,
		preventDefault: !0
	}
], wh = class {
	constructor(e) {
		this.view = e;
		let t = this.query = e.state.field(ah).query.spec;
		this.commit = this.commit.bind(this), this.searchField = I("input", {
			value: t.search,
			placeholder: Th(e, "Find"),
			"aria-label": Th(e, "Find"),
			class: "cm-textfield",
			name: "search",
			form: "",
			"main-field": "true",
			onchange: this.commit,
			onkeyup: this.commit
		}), this.replaceField = I("input", {
			value: t.replace,
			placeholder: Th(e, "Replace"),
			"aria-label": Th(e, "Replace"),
			class: "cm-textfield",
			name: "replace",
			form: "",
			onchange: this.commit,
			onkeyup: this.commit
		}), this.caseField = I("input", {
			type: "checkbox",
			name: "case",
			form: "",
			checked: t.caseSensitive,
			onchange: this.commit
		}), this.reField = I("input", {
			type: "checkbox",
			name: "re",
			form: "",
			checked: t.regexp,
			onchange: this.commit
		}), this.wordField = I("input", {
			type: "checkbox",
			name: "word",
			form: "",
			checked: t.wholeWord,
			onchange: this.commit
		});
		function n(e, t, n) {
			return I("button", {
				class: "cm-button",
				name: e,
				onclick: t,
				type: "button"
			}, n);
		}
		this.dom = I("div", {
			onkeydown: (e) => this.keydown(e),
			class: "cm-search"
		}, [
			this.searchField,
			n("next", () => dh(e), [Th(e, "next")]),
			n("prev", () => fh(e), [Th(e, "previous")]),
			n("select", () => ph(e), [Th(e, "all")]),
			I("label", null, [this.caseField, Th(e, "match case")]),
			I("label", null, [this.reField, Th(e, "regexp")]),
			I("label", null, [this.wordField, Th(e, "by word")]),
			...e.state.readOnly ? [] : [
				I("br"),
				this.replaceField,
				n("replace", () => hh(e), [Th(e, "replace")]),
				n("replaceAll", () => gh(e), [Th(e, "replace all")])
			],
			I("button", {
				name: "close",
				onclick: () => Sh(e),
				"aria-label": Th(e, "close"),
				type: "button"
			}, ["×"])
		]);
	}
	commit() {
		let e = new Gm({
			search: this.searchField.value,
			caseSensitive: this.caseField.checked,
			regexp: this.reField.checked,
			wholeWord: this.wordField.checked,
			replace: this.replaceField.value
		});
		e.eq(this.query) || (this.query = e, this.view.dispatch({ effects: rh.of(e) }));
	}
	keydown(e) {
		ys(this.view, e, "search-panel") ? e.preventDefault() : e.keyCode == 13 && e.target == this.searchField ? (e.preventDefault(), (e.shiftKey ? fh : dh)(this.view)) : e.keyCode == 13 && e.target == this.replaceField && (e.preventDefault(), hh(this.view));
	}
	update(e) {
		for (let t of e.transactions) for (let e of t.effects) e.is(rh) && !e.value.eq(this.query) && this.setQuery(e.value);
	}
	setQuery(e) {
		this.query = e, this.searchField.value = e.search, this.replaceField.value = e.replace, this.caseField.checked = e.caseSensitive, this.reField.checked = e.regexp, this.wordField.checked = e.wholeWord;
	}
	mount() {
		this.searchField.select();
	}
	get pos() {
		return 80;
	}
	get top() {
		return this.view.state.facet(Wm).top;
	}
};
function Th(e, t) {
	return e.state.phrase(t);
}
var Eh = 30, Dh = /[\s\.,:;?!]/;
function Oh(e, { from: t, to: n }) {
	let r = e.state.doc.lineAt(t), i = e.state.doc.lineAt(n).to, a = Math.max(r.from, t - Eh), o = Math.min(i, n + Eh), s = e.state.sliceDoc(a, o);
	if (a != r.from) {
		for (let e = 0; e < Eh; e++) if (!Dh.test(s[e + 1]) && Dh.test(s[e])) {
			s = s.slice(e);
			break;
		}
	}
	if (o != i) {
		for (let e = s.length - 1; e > s.length - Eh; e--) if (!Dh.test(s[e - 1]) && Dh.test(s[e])) {
			s = s.slice(0, e);
			break;
		}
	}
	return J.announce.of(`${e.state.phrase("current match")}. ${s} ${e.state.phrase("on line")} ${r.number}.`);
}
var kh = /*@__PURE__*/ J.baseTheme({
	".cm-panel.cm-search": {
		padding: "2px 6px 4px",
		position: "relative",
		"& [name=close]": {
			position: "absolute",
			top: "0",
			right: "4px",
			backgroundColor: "inherit",
			border: "none",
			font: "inherit",
			padding: 0,
			margin: 0
		},
		"& input, & button, & label": { margin: ".2em .6em .2em 0" },
		"& input[type=checkbox]": { marginRight: ".2em" },
		"& label": {
			fontSize: "80%",
			whiteSpace: "pre"
		}
	},
	"&light .cm-searchMatch": { backgroundColor: "#ffff0054" },
	"&dark .cm-searchMatch": { backgroundColor: "#00ffff8a" },
	"&light .cm-searchMatch-selected": { backgroundColor: "#ff6a0054" },
	"&dark .cm-searchMatch-selected": { backgroundColor: "#ff00ff8a" }
}), Ah = [
	ah,
	/*@__PURE__*/ nt.low(lh),
	kh
], jh = class {
	constructor(e, t, n, r) {
		this.state = e, this.pos = t, this.explicit = n, this.view = r, this.abortListeners = [], this.abortOnDocChange = !1;
	}
	tokenBefore(e) {
		let t = Z(this.state).resolveInner(this.pos, -1);
		for (; t && e.indexOf(t.name) < 0;) t = t.parent;
		return t ? {
			from: t.from,
			to: this.pos,
			text: this.state.sliceDoc(t.from, this.pos),
			type: t.type
		} : null;
	}
	matchBefore(e) {
		let t = this.state.doc.lineAt(this.pos), n = Math.max(t.from, this.pos - 250), r = t.text.slice(n - t.from, this.pos - t.from), i = r.search(Lh(e, !1));
		return i < 0 ? null : {
			from: n + i,
			to: this.pos,
			text: r.slice(i)
		};
	}
	get aborted() {
		return this.abortListeners == null;
	}
	addEventListener(e, t, n) {
		e == "abort" && this.abortListeners && (this.abortListeners.push(t), n && n.onDocChange && (this.abortOnDocChange = !0));
	}
};
function Mh(e) {
	let t = Object.keys(e).join(""), n = /\w/.test(t);
	return n && (t = t.replace(/\w/g, "")), `[${n ? "\\w" : ""}${t.replace(/[^\w\s]/g, "\\$&")}]`;
}
function Nh(e) {
	let t = Object.create(null), n = Object.create(null);
	for (let { label: r } of e) {
		t[r[0]] = !0;
		for (let e = 1; e < r.length; e++) n[r[e]] = !0;
	}
	let r = Mh(t) + Mh(n) + "*$";
	return [RegExp("^" + r), new RegExp(r)];
}
function Ph(e) {
	let t = e.map((e) => typeof e == "string" ? { label: e } : e), [n, r] = t.every((e) => /^\w+$/.test(e.label)) ? [/\w*$/, /\w+$/] : Nh(t);
	return (e) => {
		let i = e.matchBefore(r);
		return i || e.explicit ? {
			from: i ? i.from : e.pos,
			options: t,
			validFor: n
		} : null;
	};
}
var Fh = class {
	constructor(e, t, n, r) {
		this.completion = e, this.source = t, this.match = n, this.score = r;
	}
};
function Ih(e) {
	return e.selection.main.from;
}
function Lh(e, t) {
	var n;
	let { source: r } = e, i = t && r[0] != "^", a = r[r.length - 1] != "$";
	return !i && !a ? e : RegExp(`${i ? "^" : ""}(?:${r})${a ? "$" : ""}`, (n = e.flags) == null ? e.ignoreCase ? "i" : "" : n);
}
var Rh = /*@__PURE__*/ _t.define();
function zh(e, t, n, r) {
	let { main: i } = e.selection, a = n - i.from, o = r - i.from;
	return vn(vn({}, e.changeByRange((s) => {
		if (s != i && n != r && e.sliceDoc(s.from + a, s.from + o) != e.sliceDoc(n, r)) return { range: s };
		let c = e.toText(t);
		return {
			changes: {
				from: s.from + a,
				to: r == i.from ? s.to : s.from + o,
				insert: c
			},
			range: D.cursor(s.from + a + c.length)
		};
	})), {}, {
		scrollIntoView: !0,
		userEvent: "input.complete"
	});
}
var Bh = /*@__PURE__*/ new WeakMap();
function Vh(e) {
	if (!Array.isArray(e)) return e;
	let t = Bh.get(e);
	return t || Bh.set(e, t = Ph(e)), t;
}
var Hh = /*@__PURE__*/ A.define(), Uh = /*@__PURE__*/ A.define(), Wh = class {
	constructor(e) {
		this.pattern = e, this.chars = [], this.folded = [], this.any = [], this.precise = [], this.byWord = [], this.score = 0, this.matched = [];
		for (let t = 0; t < e.length;) {
			let n = Pe(e, t), r = Ie(n);
			this.chars.push(n);
			let i = e.slice(t, t + r), a = i.toUpperCase();
			this.folded.push(Pe(a == i ? i.toLowerCase() : a, 0)), t += r;
		}
		this.astral = e.length != this.chars.length;
	}
	ret(e, t) {
		return this.score = e, this.matched = t, this;
	}
	match(e) {
		if (this.pattern.length == 0) return this.ret(-100, []);
		if (e.length < this.pattern.length) return null;
		let { chars: t, folded: n, any: r, precise: i, byWord: a } = this;
		if (t.length == 1) {
			let r = Pe(e, 0), i = Ie(r), a = i == e.length ? 0 : -100;
			if (r != t[0]) {
				if (r == n[0]) a += -200;
				else return null;
			}
			return this.ret(a, [0, i]);
		}
		let o = e.indexOf(this.pattern);
		if (o == 0) return this.ret(e.length == this.pattern.length ? 0 : -100, [0, this.pattern.length]);
		let s = t.length, c = 0;
		if (o < 0) {
			for (let i = 0, a = Math.min(e.length, 200); i < a && c < s;) {
				let a = Pe(e, i);
				(a == t[c] || a == n[c]) && (r[c++] = i), i += Ie(a);
			}
			if (c < s) return null;
		}
		let l = 0, u = 0, d = !1, f = 0, p = -1, m = -1, h = /[a-z]/.test(e), g = !0;
		for (let r = 0, c = Math.min(e.length, 200), _ = 0; r < c && u < s;) {
			let c = Pe(e, r);
			o < 0 && (l < s && c == t[l] && (i[l++] = r), f < s && (c == t[f] || c == n[f] ? (f == 0 && (p = r), m = r + 1, f++) : f = 0));
			let v, y = c < 255 ? c >= 48 && c <= 57 || c >= 97 && c <= 122 ? 2 : +(c >= 65 && c <= 90) : (v = Fe(c)) == v.toLowerCase() ? v == v.toUpperCase() ? 0 : 2 : 1;
			(!r || y == 1 && h || _ == 0 && y != 0) && (t[u] == c || n[u] == c && (d = !0) ? a[u++] = r : a.length && (g = !1)), _ = y, r += Ie(c);
		}
		return u == s && a[0] == 0 && g ? this.result(-100 + (d ? -200 : 0), a, e) : f == s && p == 0 ? this.ret(-200 - e.length + (m == e.length ? 0 : -100), [0, m]) : o > -1 ? this.ret(-700 - e.length, [o, o + this.pattern.length]) : f == s ? this.ret(-900 - e.length, [p, m]) : u == s ? this.result(-100 + (d ? -200 : 0) + -700 + (g ? 0 : -1100), a, e) : t.length == 2 ? null : this.result((r[0] ? -700 : 0) + -200 + -1100, r, e);
	}
	result(e, t, n) {
		let r = [], i = 0;
		for (let e of t) {
			let t = e + (this.astral ? Ie(Pe(n, e)) : 1);
			i && r[i - 1] == e ? r[i - 1] = t : (r[i++] = e, r[i++] = t);
		}
		return this.ret(e - n.length, r);
	}
}, Gh = class {
	constructor(e) {
		this.pattern = e, this.matched = [], this.score = 0, this.folded = e.toLowerCase();
	}
	match(e) {
		if (e.length < this.pattern.length) return null;
		let t = e.slice(0, this.pattern.length), n = t == this.pattern ? 0 : t.toLowerCase() == this.folded ? -200 : null;
		return n == null ? null : (this.matched = [0, t.length], this.score = n + (e.length == this.pattern.length ? 0 : -100), this);
	}
}, $ = /*@__PURE__*/ O.define({ combine(e) {
	return Mt(e, {
		activateOnTyping: !0,
		activateOnCompletion: () => !1,
		activateOnTypingDelay: 100,
		selectOnOpen: !0,
		override: null,
		closeOnBlur: !0,
		maxRenderedOptions: 100,
		defaultKeymap: !0,
		tooltipClass: () => "",
		optionClass: () => "",
		aboveCursor: !1,
		icons: !0,
		addToOptions: [],
		positionInfo: qh,
		filterStrict: !1,
		compareCompletions: (e, t) => (e.sortText || e.label).localeCompare(t.sortText || t.label),
		interactionDelay: 75,
		updateSyncTime: 100
	}, {
		defaultKeymap: (e, t) => e && t,
		closeOnBlur: (e, t) => e && t,
		icons: (e, t) => e && t,
		tooltipClass: (e, t) => (n) => Kh(e(n), t(n)),
		optionClass: (e, t) => (n) => Kh(e(n), t(n)),
		addToOptions: (e, t) => e.concat(t),
		filterStrict: (e, t) => e || t
	});
} });
function Kh(e, t) {
	return e ? t ? e + " " + t : e : t;
}
function qh(e, t, n, r, i, a) {
	let o = e.textDirection == V.RTL, s = o, c = !1, l = "top", u, d, f = t.left - i.left, p = i.right - t.right, m = r.right - r.left, h = r.bottom - r.top;
	if (s && f < Math.min(m, p) ? s = !1 : !s && p < Math.min(m, f) && (s = !0), m <= (s ? f : p)) u = Math.max(i.top, Math.min(n.top, i.bottom - h)) - t.top, d = Math.min(400, s ? f : p);
	else {
		c = !0, d = Math.min(400, (o ? t.right : i.right - t.left) - 30);
		let e = i.bottom - t.bottom;
		e >= h || e > t.top ? u = n.bottom - t.top : (l = "bottom", u = t.bottom - n.top);
	}
	let g = (t.bottom - t.top) / a.offsetHeight, _ = (t.right - t.left) / a.offsetWidth;
	return {
		style: `${l}: ${u / g}px; max-width: ${d / _}px`,
		class: "cm-completionInfo-" + (c ? o ? "left-narrow" : "right-narrow" : s ? "left" : "right")
	};
}
var Jh = /*@__PURE__*/ A.define();
function Yh(e) {
	let t = e.addToOptions.slice();
	return e.icons && t.push({
		render(e) {
			let t = document.createElement("div");
			return t.classList.add("cm-completionIcon"), e.type && t.classList.add(...e.type.split(/\s+/g).map((e) => "cm-completionIcon-" + e)), t.setAttribute("aria-hidden", "true"), t;
		},
		position: 20
	}), t.push({
		render(e, t, n, r) {
			let i = document.createElement("span");
			i.className = "cm-completionLabel";
			let a = e.displayLabel || e.label, o = 0;
			for (let e = 0; e < r.length;) {
				let t = r[e++], n = r[e++];
				t > o && i.appendChild(document.createTextNode(a.slice(o, t)));
				let s = i.appendChild(document.createElement("span"));
				s.appendChild(document.createTextNode(a.slice(t, n))), s.className = "cm-completionMatchedText", o = n;
			}
			return o < a.length && i.appendChild(document.createTextNode(a.slice(o))), i;
		},
		position: 50
	}, {
		render(e) {
			if (!e.detail) return null;
			let t = document.createElement("span");
			return t.className = "cm-completionDetail", t.textContent = e.detail, t;
		},
		position: 80
	}), t.sort((e, t) => e.position - t.position).map((e) => e.render);
}
function Xh(e, t, n) {
	if (e <= n) return {
		from: 0,
		to: e
	};
	if (t < 0 && (t = 0), t <= e >> 1) {
		let e = Math.floor(t / n);
		return {
			from: e * n,
			to: (e + 1) * n
		};
	}
	let r = Math.ceil((e - t) / n);
	return {
		from: e - r * n,
		to: e - (r - 1) * n
	};
}
var Zh = class {
	constructor(e, t, n) {
		this.view = e, this.stateField = t, this.applyCompletion = n, this.info = null, this.infoDestroy = null, this.placeInfoReq = {
			read: () => this.measureInfo(),
			write: (e) => this.placeInfo(e),
			key: this
		}, this.space = null, this.currentClass = "";
		let r = e.state.field(t), { options: i, selected: a } = r.open, o = e.state.facet($);
		this.optionContent = Yh(o), this.optionClass = o.optionClass, this.tooltipClass = o.tooltipClass, this.range = Xh(i.length, a, o.maxRenderedOptions), this.dom = document.createElement("div"), this.dom.className = "cm-tooltip-autocomplete", this.updateTooltipClass(e.state), this.dom.addEventListener("mousedown", (n) => {
			let { options: r } = e.state.field(t).open;
			for (let t = n.target, i; t && t != this.dom; t = t.parentNode) if (t.nodeName == "LI" && (i = /-(\d+)$/.exec(t.id)) && +i[1] < r.length) {
				this.applyCompletion(e, r[+i[1]]), n.preventDefault();
				return;
			}
			if (n.target == this.list) {
				let t = this.list.classList.contains("cm-completionListIncompleteTop") && n.clientY < this.list.firstChild.getBoundingClientRect().top ? this.range.from - 1 : this.list.classList.contains("cm-completionListIncompleteBottom") && n.clientY > this.list.lastChild.getBoundingClientRect().bottom ? this.range.to : null;
				t != null && (e.dispatch({ effects: Jh.of(t) }), n.preventDefault());
			}
		}), this.dom.addEventListener("focusout", (t) => {
			let n = e.state.field(this.stateField, !1);
			n && n.tooltip && e.state.facet($).closeOnBlur && t.relatedTarget != e.contentDOM && e.dispatch({ effects: Uh.of(null) });
		}), this.showOptions(i, r.id);
	}
	mount() {
		this.updateSel();
	}
	showOptions(e, t) {
		this.list && this.list.remove(), this.list = this.dom.appendChild(this.createListBox(e, t, this.range)), this.list.addEventListener("scroll", () => {
			this.info && this.view.requestMeasure(this.placeInfoReq);
		});
	}
	update(e) {
		var t;
		let n = e.state.field(this.stateField), r = e.startState.field(this.stateField);
		if (this.updateTooltipClass(e.state), n != r) {
			let { options: i, selected: a, disabled: o } = n.open;
			(!r.open || r.open.options != i) && (this.range = Xh(i.length, a, e.state.facet($).maxRenderedOptions), this.showOptions(i, n.id)), this.updateSel(), o != ((t = r.open) == null ? void 0 : t.disabled) && this.dom.classList.toggle("cm-tooltip-autocomplete-disabled", !!o);
		}
	}
	updateTooltipClass(e) {
		let t = this.tooltipClass(e);
		if (t != this.currentClass) {
			for (let e of this.currentClass.split(" ")) e && this.dom.classList.remove(e);
			for (let e of t.split(" ")) e && this.dom.classList.add(e);
			this.currentClass = t;
		}
	}
	positioned(e) {
		this.space = e, this.info && this.view.requestMeasure(this.placeInfoReq);
	}
	updateSel() {
		let e = this.view.state.field(this.stateField), t = e.open;
		(t.selected > -1 && t.selected < this.range.from || t.selected >= this.range.to) && (this.range = Xh(t.options.length, t.selected, this.view.state.facet($).maxRenderedOptions), this.showOptions(t.options, e.id));
		let n = this.updateSelectedOption(t.selected);
		if (n) {
			this.destroyInfo();
			let { completion: r } = t.options[t.selected], { info: i } = r;
			if (!i) return;
			let a = typeof i == "string" ? document.createTextNode(i) : i(r);
			if (!a) return;
			"then" in a ? a.then((t) => {
				t && this.view.state.field(this.stateField, !1) == e && this.addInfoPane(t, r);
			}).catch((e) => U(this.view.state, e, "completion info")) : (this.addInfoPane(a, r), n.setAttribute("aria-describedby", this.info.id));
		}
	}
	addInfoPane(e, t) {
		this.destroyInfo();
		let n = this.info = document.createElement("div");
		if (n.className = "cm-tooltip cm-completionInfo", n.id = "cm-completionInfo-" + Math.floor(Math.random() * 65535).toString(16), e.nodeType != null) n.appendChild(e), this.infoDestroy = null;
		else {
			let { dom: t, destroy: r } = e;
			n.appendChild(t), this.infoDestroy = r || null;
		}
		this.dom.appendChild(n), this.view.requestMeasure(this.placeInfoReq);
	}
	updateSelectedOption(e) {
		let t = null;
		for (let n = this.list.firstChild, r = this.range.from; n; n = n.nextSibling, r++) n.nodeName != "LI" || !n.id ? r-- : r == e ? n.hasAttribute("aria-selected") || (n.setAttribute("aria-selected", "true"), t = n) : n.hasAttribute("aria-selected") && (n.removeAttribute("aria-selected"), n.removeAttribute("aria-describedby"));
		return t && $h(this.list, t), t;
	}
	measureInfo() {
		let e = this.dom.querySelector("[aria-selected]");
		if (!e || !this.info) return null;
		let t = this.dom.getBoundingClientRect(), n = this.info.getBoundingClientRect(), r = e.getBoundingClientRect(), i = this.space;
		if (!i) {
			let e = this.dom.ownerDocument.documentElement;
			i = {
				left: 0,
				top: 0,
				right: e.clientWidth,
				bottom: e.clientHeight
			};
		}
		return r.top > Math.min(i.bottom, t.bottom) - 10 || r.bottom < Math.max(i.top, t.top) + 10 ? null : this.view.state.facet($).positionInfo(this.view, t, r, n, i, this.dom);
	}
	placeInfo(e) {
		this.info && (e ? (e.style && (this.info.style.cssText = e.style), this.info.className = "cm-tooltip cm-completionInfo " + (e.class || "")) : this.info.style.cssText = "top: -1e6px");
	}
	createListBox(e, t, n) {
		let r = document.createElement("ul");
		r.id = t, r.setAttribute("role", "listbox"), r.setAttribute("aria-expanded", "true"), r.setAttribute("aria-label", this.view.state.phrase("Completions")), r.addEventListener("mousedown", (e) => {
			e.target == r && e.preventDefault();
		});
		let i = null;
		for (let a = n.from; a < n.to; a++) {
			let { completion: o, match: s } = e[a], { section: c } = o;
			if (c) {
				let e = typeof c == "string" ? c : c.name;
				if (e != i && (a > n.from || n.from == 0)) {
					if (i = e, typeof c != "string" && c.header) r.appendChild(c.header(c));
					else {
						let t = r.appendChild(document.createElement("completion-section"));
						t.textContent = e;
					}
				}
			}
			let l = r.appendChild(document.createElement("li"));
			l.id = t + "-" + a, l.setAttribute("role", "option");
			let u = this.optionClass(o);
			u && (l.className = u);
			for (let e of this.optionContent) {
				let t = e(o, this.view.state, this.view, s);
				t && l.appendChild(t);
			}
		}
		return n.from && r.classList.add("cm-completionListIncompleteTop"), n.to < e.length && r.classList.add("cm-completionListIncompleteBottom"), r;
	}
	destroyInfo() {
		this.info && (this.infoDestroy && this.infoDestroy(), this.info.remove(), this.info = null);
	}
	destroy() {
		this.destroyInfo();
	}
};
function Qh(e, t) {
	return (n) => new Zh(n, e, t);
}
function $h(e, t) {
	let n = e.getBoundingClientRect(), r = t.getBoundingClientRect(), i = n.height / e.offsetHeight;
	r.top < n.top ? e.scrollTop -= (n.top - r.top) / i : r.bottom > n.bottom && (e.scrollTop += (r.bottom - n.bottom) / i);
}
function eg(e) {
	return (e.boost || 0) * 100 + (e.apply ? 10 : 0) + (e.info ? 5 : 0) + +!!e.type;
}
function tg(e, t) {
	let n = [], r = null, i = null, a = (e) => {
		n.push(e);
		let { section: t } = e.completion;
		if (t) {
			r || (r = []);
			let e = typeof t == "string" ? t : t.name;
			r.some((t) => t.name == e) || r.push(typeof t == "string" ? { name: e } : t);
		}
	}, o = t.facet($);
	for (let r of e) if (r.hasResult()) {
		let e = r.result.getMatch;
		if (r.result.filter === !1) for (let t of r.result.options) a(new Fh(t, r.source, e ? e(t) : [], 1e9 - n.length));
		else {
			let n = t.sliceDoc(r.from, r.to), s, c = o.filterStrict ? new Gh(n) : new Wh(n);
			for (let t of r.result.options) if (s = c.match(t.label)) {
				let n = t.displayLabel ? e ? e(t, s.matched) : [] : s.matched, o = s.score + (t.boost || 0);
				if (a(new Fh(t, r.source, n, o)), typeof t.section == "object" && t.section.rank === "dynamic") {
					let { name: e } = t.section;
					i || (i = Object.create(null)), i[e] = Math.max(o, i[e] || -1e9);
				}
			}
		}
	}
	if (r) {
		let e = Object.create(null), t = 0, a = (e, t) => (e.rank === "dynamic" && t.rank === "dynamic" ? i[t.name] - i[e.name] : 0) || (typeof e.rank == "number" ? e.rank : 1e9) - (typeof t.rank == "number" ? t.rank : 1e9) || (e.name < t.name ? -1 : 1);
		for (let n of r.sort(a)) t -= 1e5, e[n.name] = t;
		for (let t of n) {
			let { section: n } = t.completion;
			n && (t.score += e[typeof n == "string" ? n : n.name]);
		}
	}
	let s = [], c = null, l = o.compareCompletions;
	for (let e of n.sort((e, t) => t.score - e.score || l(e.completion, t.completion))) {
		let t = e.completion;
		!c || c.label != t.label || c.detail != t.detail || c.type != null && t.type != null && c.type != t.type || c.apply != t.apply || c.boost != t.boost ? s.push(e) : eg(e.completion) > eg(c) && (s[s.length - 1] = e), c = e.completion;
	}
	return s;
}
var ng = class e {
	constructor(e, t, n, r, i, a) {
		this.options = e, this.attrs = t, this.tooltip = n, this.timestamp = r, this.selected = i, this.disabled = a;
	}
	setSelected(t, n) {
		return t == this.selected || t >= this.options.length ? this : new e(this.options, sg(n, t), this.tooltip, this.timestamp, t, this.disabled);
	}
	static build(t, n, r, i, a, o) {
		if (i && !o && t.some((e) => e.isPending)) return i.setDisabled();
		let s = tg(t, n);
		if (!s.length) return i && t.some((e) => e.isPending) ? i.setDisabled() : null;
		let c = n.facet($).selectOnOpen ? 0 : -1;
		if (i && i.selected != c && i.selected != -1) {
			let e = i.options[i.selected].completion;
			for (let t = 0; t < s.length; t++) if (s[t].completion == e) {
				c = t;
				break;
			}
		}
		return new e(s, sg(r, c), {
			pos: t.reduce((e, t) => t.hasResult() ? Math.min(e, t.from) : e, 1e8),
			create: gg,
			above: a.aboveCursor
		}, i ? i.timestamp : Date.now(), c, !1);
	}
	map(t) {
		return new e(this.options, this.attrs, vn(vn({}, this.tooltip), {}, { pos: t.mapPos(this.tooltip.pos) }), this.timestamp, this.selected, this.disabled);
	}
	setDisabled() {
		return new e(this.options, this.attrs, this.tooltip, this.timestamp, this.selected, !0);
	}
}, rg = class e {
	constructor(e, t, n) {
		this.active = e, this.id = t, this.open = n;
	}
	static start() {
		return new e(cg, "cm-ac-" + Math.floor(Math.random() * 2e6).toString(36), null);
	}
	update(t) {
		let { state: n } = t, r = n.facet($), i = (r.override || n.languageDataAt("autocomplete", Ih(n)).map(Vh)).map((e) => (this.active.find((t) => t.source == e) || new ug(e, +!!this.active.some((e) => e.state != 0))).update(t, r));
		i.length == this.active.length && i.every((e, t) => e == this.active[t]) && (i = this.active);
		let a = this.open, o = t.effects.some((e) => e.is(pg));
		a && t.docChanged && (a = a.map(t.changes)), t.selection || i.some((e) => e.hasResult() && t.changes.touchesRange(e.from, e.to)) || !ig(i, this.active) || o ? a = ng.build(i, n, this.id, a, r, o) : a && a.disabled && !i.some((e) => e.isPending) && (a = null), !a && i.every((e) => !e.isPending) && i.some((e) => e.hasResult()) && (i = i.map((e) => e.hasResult() ? new ug(e.source, 0) : e));
		for (let e of t.effects) e.is(Jh) && (a = a && a.setSelected(e.value, this.id));
		return i == this.active && a == this.open ? this : new e(i, this.id, a);
	}
	get tooltip() {
		return this.open ? this.open.tooltip : null;
	}
	get attrs() {
		return this.open ? this.open.attrs : this.active.length ? ag : og;
	}
};
function ig(e, t) {
	if (e == t) return !0;
	for (let n = 0, r = 0;;) {
		for (; n < e.length && !e[n].hasResult();) n++;
		for (; r < t.length && !t[r].hasResult();) r++;
		let i = n == e.length, a = r == t.length;
		if (i || a) return i == a;
		if (e[n++].result != t[r++].result) return !1;
	}
}
var ag = { "aria-autocomplete": "list" }, og = {};
function sg(e, t) {
	let n = {
		"aria-autocomplete": "list",
		"aria-haspopup": "listbox",
		"aria-controls": e
	};
	return t > -1 && (n["aria-activedescendant"] = e + "-" + t), n;
}
var cg = [];
function lg(e, t) {
	if (e.isUserEvent("input.complete")) {
		let n = e.annotation(Rh);
		if (n && t.activateOnCompletion(n)) return 12;
	}
	let n = e.isUserEvent("input.type");
	return n && t.activateOnTyping ? 5 : n ? 1 : e.isUserEvent("delete.backward") ? 2 : e.selection ? 8 : e.docChanged ? 16 : 0;
}
var ug = class e {
	constructor(e, t, n = !1) {
		this.source = e, this.state = t, this.explicit = n;
	}
	hasResult() {
		return !1;
	}
	get isPending() {
		return this.state == 1;
	}
	update(t, n) {
		let r = lg(t, n), i = this;
		(r & 8 || r & 16 && this.touches(t)) && (i = new e(i.source, 0)), r & 4 && i.state == 0 && (i = new e(this.source, 1)), i = i.updateFor(t, r);
		for (let n of t.effects) if (n.is(Hh)) i = new e(i.source, 1, n.value);
		else if (n.is(Uh)) i = new e(i.source, 0);
		else if (n.is(pg)) for (let e of n.value) e.source == i.source && (i = e);
		return i;
	}
	updateFor(e, t) {
		return this.map(e.changes);
	}
	map(e) {
		return this;
	}
	touches(e) {
		return e.changes.touchesRange(Ih(e.state));
	}
}, dg = class e extends ug {
	constructor(e, t, n, r, i, a) {
		super(e, 3, t), this.limit = n, this.result = r, this.from = i, this.to = a;
	}
	hasResult() {
		return !0;
	}
	updateFor(t, n) {
		var r;
		if (!(n & 3)) return this.map(t.changes);
		let i = this.result;
		i.map && !t.changes.empty && (i = i.map(i, t.changes));
		let a = t.changes.mapPos(this.from), o = t.changes.mapPos(this.to, 1), s = Ih(t.state);
		if (s > o || !i || n & 2 && (Ih(t.startState) == this.from || s < this.limit)) return new ug(this.source, n & 4 ? 1 : 0);
		let c = t.changes.mapPos(this.limit);
		return fg(i.validFor, t.state, a, o) ? new e(this.source, this.explicit, c, i, a, o) : i.update && (i = i.update(i, a, o, new jh(t.state, s, !1))) ? new e(this.source, this.explicit, c, i, i.from, (r = i.to) == null ? Ih(t.state) : r) : new ug(this.source, 1, this.explicit);
	}
	map(t) {
		if (t.empty) return this;
		let n = this.result.map ? this.result.map(this.result, t) : this.result;
		return n ? new e(this.source, this.explicit, t.mapPos(this.limit), n, t.mapPos(this.from), t.mapPos(this.to, 1)) : new ug(this.source, 0);
	}
	touches(e) {
		return e.changes.touchesRange(this.from, this.to);
	}
};
function fg(e, t, n, r) {
	if (!e) return !1;
	let i = t.sliceDoc(n, r);
	return typeof e == "function" ? e(i, n, r, t) : Lh(e, !0).test(i);
}
var pg = /*@__PURE__*/ A.define({ map(e, t) {
	return e.map((e) => e.map(t));
} }), mg = /*@__PURE__*/ k.define({
	create() {
		return rg.start();
	},
	update(e, t) {
		return e.update(t);
	},
	provide: (e) => [Oc.from(e, (e) => e.tooltip), J.contentAttributes.from(e, (e) => e.attrs)]
});
function hg(e, t) {
	let n = t.completion.apply || t.completion.label, r = e.state.field(mg).active.find((e) => e.source == t.source);
	return r instanceof dg && (typeof n == "string" ? e.dispatch(vn(vn({}, zh(e.state, n, r.from, r.to)), {}, { annotations: Rh.of(t.completion) })) : n(e, t.completion, r.from, r.to), !0);
}
var gg = /*@__PURE__*/ Qh(mg, hg);
function _g(e, t = "option") {
	return (n) => {
		let r = n.state.field(mg, !1);
		if (!r || !r.open || r.open.disabled || Date.now() - r.open.timestamp < n.state.facet($).interactionDelay) return !1;
		let i = 1, a;
		t == "page" && (a = zc(n, r.open.tooltip)) && (i = Math.max(2, Math.floor(a.dom.offsetHeight / a.dom.querySelector("li").offsetHeight) - 1));
		let { length: o } = r.open.options, s = r.open.selected > -1 ? r.open.selected + i * (e ? 1 : -1) : e ? 0 : o - 1;
		return s < 0 ? s = t == "page" ? 0 : o - 1 : s >= o && (s = t == "page" ? o - 1 : 0), n.dispatch({ effects: Jh.of(s) }), !0;
	};
}
var vg = (e) => {
	let t = e.state.field(mg, !1);
	return e.state.readOnly || !t || !t.open || t.open.selected < 0 || t.open.disabled || Date.now() - t.open.timestamp < e.state.facet($).interactionDelay ? !1 : hg(e, t.open.options[t.open.selected]);
}, yg = (e) => e.state.field(mg, !1) ? (e.dispatch({ effects: Hh.of(!0) }), !0) : !1, bg = (e) => {
	let t = e.state.field(mg, !1);
	return !t || !t.active.some((e) => e.state != 0) ? !1 : (e.dispatch({ effects: Uh.of(null) }), !0);
}, xg = class {
	constructor(e, t) {
		this.active = e, this.context = t, this.time = Date.now(), this.updates = [], this.done = void 0;
	}
}, Sg = 50, Cg = 1e3, wg = /*@__PURE__*/ W.fromClass(class {
	constructor(e) {
		this.view = e, this.debounceUpdate = -1, this.running = [], this.debounceAccept = -1, this.pendingStart = !1, this.composing = 0;
		for (let t of e.state.field(mg).active) t.isPending && this.startQuery(t);
	}
	update(e) {
		let t = e.state.field(mg), n = e.state.facet($);
		if (!e.selectionSet && !e.docChanged && e.startState.field(mg) == t) return;
		let r = e.transactions.some((e) => {
			let t = lg(e, n);
			return t & 8 || (e.selection || e.docChanged) && !(t & 3);
		});
		for (let t = 0; t < this.running.length; t++) {
			let n = this.running[t];
			if (r || n.context.abortOnDocChange && e.docChanged || n.updates.length + e.transactions.length > Sg && Date.now() - n.time > Cg) {
				for (let e of n.context.abortListeners) try {
					e();
				} catch (e) {
					U(this.view.state, e);
				}
				n.context.abortListeners = null, this.running.splice(t--, 1);
			} else n.updates.push(...e.transactions);
		}
		this.debounceUpdate > -1 && clearTimeout(this.debounceUpdate), e.transactions.some((e) => e.effects.some((e) => e.is(Hh))) && (this.pendingStart = !0);
		let i = this.pendingStart ? 50 : n.activateOnTypingDelay;
		if (this.debounceUpdate = t.active.some((e) => e.isPending && !this.running.some((t) => t.active.source == e.source)) ? setTimeout(() => this.startUpdate(), i) : -1, this.composing != 0) for (let t of e.transactions) t.isUserEvent("input.type") ? this.composing = 2 : this.composing == 2 && t.selection && (this.composing = 3);
	}
	startUpdate() {
		this.debounceUpdate = -1, this.pendingStart = !1;
		let { state: e } = this.view, t = e.field(mg);
		for (let e of t.active) e.isPending && !this.running.some((t) => t.active.source == e.source) && this.startQuery(e);
		this.running.length && t.open && t.open.disabled && (this.debounceAccept = setTimeout(() => this.accept(), this.view.state.facet($).updateSyncTime));
	}
	startQuery(e) {
		let { state: t } = this.view, n = new jh(t, Ih(t), e.explicit, this.view), r = new xg(e, n);
		this.running.push(r), Promise.resolve(e.source(n)).then((e) => {
			r.context.aborted || (r.done = e || null, this.scheduleAccept());
		}, (e) => {
			this.view.dispatch({ effects: Uh.of(null) }), U(this.view.state, e);
		});
	}
	scheduleAccept() {
		this.running.every((e) => e.done !== void 0) ? this.accept() : this.debounceAccept < 0 && (this.debounceAccept = setTimeout(() => this.accept(), this.view.state.facet($).updateSyncTime));
	}
	accept() {
		var e;
		this.debounceAccept > -1 && clearTimeout(this.debounceAccept), this.debounceAccept = -1;
		let t = [], n = this.view.state.facet($), r = this.view.state.field(mg);
		for (let i = 0; i < this.running.length; i++) {
			let a = this.running[i];
			if (a.done === void 0) continue;
			if (this.running.splice(i--, 1), a.done) {
				let r = Ih(a.updates.length ? a.updates[0].startState : this.view.state), i = Math.min(r, a.done.from + +!a.active.explicit), o = new dg(a.active.source, a.active.explicit, i, a.done, a.done.from, (e = a.done.to) == null ? r : e);
				for (let e of a.updates) o = o.update(e, n);
				if (o.hasResult()) {
					t.push(o);
					continue;
				}
			}
			let o = r.active.find((e) => e.source == a.active.source);
			if (o && o.isPending) {
				if (a.done == null) {
					let e = new ug(a.active.source, 0);
					for (let t of a.updates) e = e.update(t, n);
					e.isPending || t.push(e);
				} else this.startQuery(o);
			}
		}
		(t.length || r.open && r.open.disabled) && this.view.dispatch({ effects: pg.of(t) });
	}
}, { eventHandlers: {
	blur(e) {
		let t = this.view.state.field(mg, !1);
		if (t && t.tooltip && this.view.state.facet($).closeOnBlur) {
			let n = t.open && zc(this.view, t.open.tooltip);
			(!n || !n.dom.contains(e.relatedTarget)) && setTimeout(() => this.view.dispatch({ effects: Uh.of(null) }), 10);
		}
	},
	compositionstart() {
		this.composing = 1;
	},
	compositionend() {
		this.composing == 3 && setTimeout(() => this.view.dispatch({ effects: Hh.of(!1) }), 20), this.composing = 0;
	}
} }), Tg = typeof navigator == "object" && /*@__PURE__*/ /Win/.test(navigator.platform), Eg = /*@__PURE__*/ nt.highest(/*@__PURE__*/ J.domEventHandlers({ keydown(e, t) {
	let n = t.state.field(mg, !1);
	if (!n || !n.open || n.open.disabled || n.open.selected < 0 || e.key.length > 1 || e.ctrlKey && !(Tg && e.altKey) || e.metaKey) return !1;
	let r = n.open.options[n.open.selected], i = n.active.find((e) => e.source == r.source), a = r.completion.commitCharacters || i.result.commitCharacters;
	return a && a.indexOf(e.key) > -1 && hg(t, r), !1;
} })), Dg = /*@__PURE__*/ J.baseTheme({
	".cm-tooltip.cm-tooltip-autocomplete": { "& > ul": {
		fontFamily: "monospace",
		whiteSpace: "nowrap",
		overflow: "hidden auto",
		maxWidth_fallback: "700px",
		maxWidth: "min(700px, 95vw)",
		minWidth: "250px",
		maxHeight: "10em",
		height: "100%",
		listStyle: "none",
		margin: 0,
		padding: 0,
		"& > li, & > completion-section": {
			padding: "1px 3px",
			lineHeight: 1.2
		},
		"& > li": {
			overflowX: "hidden",
			textOverflow: "ellipsis",
			cursor: "pointer"
		},
		"& > completion-section": {
			display: "list-item",
			borderBottom: "1px solid silver",
			paddingLeft: "0.5em",
			opacity: .7
		}
	} },
	"&light .cm-tooltip-autocomplete ul li[aria-selected]": {
		background: "#17c",
		color: "white"
	},
	"&light .cm-tooltip-autocomplete-disabled ul li[aria-selected]": { background: "#777" },
	"&dark .cm-tooltip-autocomplete ul li[aria-selected]": {
		background: "#347",
		color: "white"
	},
	"&dark .cm-tooltip-autocomplete-disabled ul li[aria-selected]": { background: "#444" },
	".cm-completionListIncompleteTop:before, .cm-completionListIncompleteBottom:after": {
		content: "\"···\"",
		opacity: .5,
		display: "block",
		textAlign: "center",
		cursor: "pointer"
	},
	".cm-tooltip.cm-completionInfo": {
		position: "absolute",
		padding: "3px 9px",
		width: "max-content",
		maxWidth: "400px",
		boxSizing: "border-box",
		whiteSpace: "pre-line"
	},
	".cm-completionInfo.cm-completionInfo-left": { right: "100%" },
	".cm-completionInfo.cm-completionInfo-right": { left: "100%" },
	".cm-completionInfo.cm-completionInfo-left-narrow": { right: "30px" },
	".cm-completionInfo.cm-completionInfo-right-narrow": { left: "30px" },
	"&light .cm-snippetField": { backgroundColor: "#00000022" },
	"&dark .cm-snippetField": { backgroundColor: "#ffffff22" },
	".cm-snippetFieldPosition": {
		verticalAlign: "text-top",
		width: 0,
		height: "1.15em",
		display: "inline-block",
		margin: "0 -0.7px -.7em",
		borderLeft: "1.4px dotted #888"
	},
	".cm-completionMatchedText": { textDecoration: "underline" },
	".cm-completionDetail": {
		marginLeft: "0.5em",
		fontStyle: "italic"
	},
	".cm-completionIcon": {
		fontSize: "90%",
		width: ".8em",
		display: "inline-block",
		textAlign: "center",
		paddingRight: ".6em",
		opacity: "0.6",
		boxSizing: "content-box"
	},
	".cm-completionIcon-function, .cm-completionIcon-method": { "&:after": { content: "'ƒ'" } },
	".cm-completionIcon-class": { "&:after": { content: "'○'" } },
	".cm-completionIcon-interface": { "&:after": { content: "'◌'" } },
	".cm-completionIcon-variable": { "&:after": { content: "'𝑥'" } },
	".cm-completionIcon-constant": { "&:after": { content: "'𝐶'" } },
	".cm-completionIcon-type": { "&:after": { content: "'𝑡'" } },
	".cm-completionIcon-enum": { "&:after": { content: "'∪'" } },
	".cm-completionIcon-property": { "&:after": { content: "'□'" } },
	".cm-completionIcon-keyword": { "&:after": { content: "'🔑︎'" } },
	".cm-completionIcon-namespace": { "&:after": { content: "'▢'" } },
	".cm-completionIcon-text": { "&:after": {
		content: "'abc'",
		fontSize: "50%",
		verticalAlign: "middle"
	} }
}), Og = {
	brackets: [
		"(",
		"[",
		"{",
		"'",
		"\""
	],
	before: ")]}:;>",
	stringPrefixes: []
}, kg = /*@__PURE__*/ A.define({ map(e, t) {
	let n = t.mapPos(e, -1, T.TrackAfter);
	return n == null ? void 0 : n;
} }), Ag = /*@__PURE__*/ new class extends Nt {}();
Ag.startSide = 1, Ag.endSide = -1;
var jg = /*@__PURE__*/ k.define({
	create() {
		return P.empty;
	},
	update(e, t) {
		if (e = e.map(t.changes), t.selection) {
			let n = t.state.doc.lineAt(t.selection.main.head);
			e = e.update({ filter: (e) => e >= n.from && e <= n.to });
		}
		for (let n of t.effects) n.is(kg) && (e = e.update({ add: [Ag.range(n.value, n.value + 1)] }));
		return e;
	}
});
function Mg() {
	return [Lg, jg];
}
var Ng = "()[]{}<>«»»«［］｛｝";
function Pg(e) {
	for (let t = 0; t < 16; t += 2) if (Ng.charCodeAt(t) == e) return Ng.charAt(t + 1);
	return Fe(e < 128 ? e : e + 1);
}
function Fg(e, t) {
	return e.languageDataAt("closeBrackets", t)[0] || Og;
}
var Ig = typeof navigator == "object" && /*@__PURE__*/ /Android\b/.test(navigator.userAgent), Lg = /*@__PURE__*/ J.inputHandler.of((e, t, n, r) => {
	if ((Ig ? e.composing : e.compositionStarted) || e.state.readOnly) return !1;
	let i = e.state.selection.main;
	if (r.length > 2 || r.length == 2 && Ie(Pe(r, 0)) == 1 || t != i.from || n != i.to) return !1;
	let a = zg(e.state, r);
	return a ? (e.dispatch(a), !0) : !1;
}), Rg = [{
	key: "Backspace",
	run: ({ state: e, dispatch: t }) => {
		if (e.readOnly) return !1;
		let n = Fg(e, e.selection.main.head).brackets || Og.brackets, r = null, i = e.changeByRange((t) => {
			if (t.empty) {
				let r = Hg(e.doc, t.head);
				for (let i of n) if (i == r && Vg(e.doc, t.head) == Pg(Pe(i, 0))) return {
					changes: {
						from: t.head - i.length,
						to: t.head + i.length
					},
					range: D.cursor(t.head - i.length)
				};
			}
			return { range: r = t };
		});
		return r || t(e.update(i, {
			scrollIntoView: !0,
			userEvent: "delete.backward"
		})), !r;
	}
}];
function zg(e, t) {
	let n = Fg(e, e.selection.main.head), r = n.brackets || Og.brackets;
	for (let i of r) {
		let a = Pg(Pe(i, 0));
		if (t == i) return a == i ? Gg(e, i, r.indexOf(i + i + i) > -1, n) : Ug(e, i, a, n.before || Og.before);
		if (t == a && Bg(e, e.selection.main.from)) return Wg(e, i, a);
	}
	return null;
}
function Bg(e, t) {
	let n = !1;
	return e.field(jg).between(0, e.doc.length, (e) => {
		e == t && (n = !0);
	}), n;
}
function Vg(e, t) {
	let n = e.sliceString(t, t + 2);
	return n.slice(0, Ie(Pe(n, 0)));
}
function Hg(e, t) {
	let n = e.sliceString(t - 2, t);
	return Ie(Pe(n, 0)) == n.length ? n : n.slice(1);
}
function Ug(e, t, n, r) {
	let i = null, a = e.changeByRange((a) => {
		if (!a.empty) return {
			changes: [{
				insert: t,
				from: a.from
			}, {
				insert: n,
				from: a.to
			}],
			effects: kg.of(a.to + t.length),
			range: D.range(a.anchor + t.length, a.head + t.length)
		};
		let o = Vg(e.doc, a.head);
		return !o || /\s/.test(o) || r.indexOf(o) > -1 ? {
			changes: {
				insert: t + n,
				from: a.head
			},
			effects: kg.of(a.head + t.length),
			range: D.cursor(a.head + t.length)
		} : { range: i = a };
	});
	return i ? null : e.update(a, {
		scrollIntoView: !0,
		userEvent: "input.type"
	});
}
function Wg(e, t, n) {
	let r = null, i = e.changeByRange((t) => t.empty && Vg(e.doc, t.head) == n ? {
		changes: {
			from: t.head,
			to: t.head + n.length,
			insert: n
		},
		range: D.cursor(t.head + n.length)
	} : r = { range: t });
	return r ? null : e.update(i, {
		scrollIntoView: !0,
		userEvent: "input.type"
	});
}
function Gg(e, t, n, r) {
	let i = r.stringPrefixes || Og.stringPrefixes, a = null, o = e.changeByRange((r) => {
		if (!r.empty) return {
			changes: [{
				insert: t,
				from: r.from
			}, {
				insert: t,
				from: r.to
			}],
			effects: kg.of(r.to + t.length),
			range: D.range(r.anchor + t.length, r.head + t.length)
		};
		let o = r.head, s = Vg(e.doc, o), c;
		if (s == t) {
			if (Kg(e, o)) return {
				changes: {
					insert: t + t,
					from: o
				},
				effects: kg.of(o + t.length),
				range: D.cursor(o + t.length)
			};
			if (Bg(e, o)) {
				let r = n && e.sliceDoc(o, o + t.length * 3) == t + t + t ? t + t + t : t;
				return {
					changes: {
						from: o,
						to: o + r.length,
						insert: r
					},
					range: D.cursor(o + r.length)
				};
			}
		} else if (n && e.sliceDoc(o - 2 * t.length, o) == t + t && (c = Jg(e, o - 2 * t.length, i)) > -1 && Kg(e, c)) return {
			changes: {
				insert: t + t + t + t,
				from: o
			},
			effects: kg.of(o + t.length),
			range: D.cursor(o + t.length)
		};
		else if (e.charCategorizer(o)(s) != M.Word && Jg(e, o, i) > -1 && !qg(e, o, t, i)) return {
			changes: {
				insert: t + t,
				from: o
			},
			effects: kg.of(o + t.length),
			range: D.cursor(o + t.length)
		};
		return { range: a = r };
	});
	return a ? null : e.update(o, {
		scrollIntoView: !0,
		userEvent: "input.type"
	});
}
function Kg(e, t) {
	let n = Z(e).resolveInner(t + 1);
	return n.parent && n.from == t;
}
function qg(e, t, n, r) {
	let i = Z(e).resolveInner(t, -1), a = r.reduce((e, t) => Math.max(e, t.length), 0);
	for (let o = 0; o < 5; o++) {
		let o = e.sliceDoc(i.from, Math.min(i.to, i.from + n.length + a)), s = o.indexOf(n);
		if (!s || s > -1 && r.indexOf(o.slice(0, s)) > -1) {
			let t = i.firstChild;
			for (; t && t.from == i.from && t.to - t.from > n.length + s;) {
				if (e.sliceDoc(t.to - n.length, t.to) == n) return !1;
				t = t.firstChild;
			}
			return !0;
		}
		let c = i.to == t && i.parent;
		if (!c) break;
		i = c;
	}
	return !1;
}
function Jg(e, t, n) {
	let r = e.charCategorizer(t);
	if (r(e.sliceDoc(t - 1, t)) != M.Word) return t;
	for (let i of n) {
		let n = t - i.length;
		if (e.sliceDoc(n, t) == i && r(e.sliceDoc(n - 1, n)) != M.Word) return n;
	}
	return -1;
}
function Yg(e = {}) {
	return [
		Eg,
		mg,
		$.of(e),
		wg,
		Zg,
		Dg
	];
}
var Xg = [
	{
		key: "Ctrl-Space",
		run: yg
	},
	{
		mac: "Alt-`",
		run: yg
	},
	{
		mac: "Alt-i",
		run: yg
	},
	{
		key: "Escape",
		run: bg
	},
	{
		key: "ArrowDown",
		run: /*@__PURE__*/ _g(!0)
	},
	{
		key: "ArrowUp",
		run: /*@__PURE__*/ _g(!1)
	},
	{
		key: "PageDown",
		run: /*@__PURE__*/ _g(!0, "page")
	},
	{
		key: "PageUp",
		run: /*@__PURE__*/ _g(!1, "page")
	},
	{
		key: "Enter",
		run: vg
	}
], Zg = /*@__PURE__*/ nt.highest(/*@__PURE__*/ gs.computeN([$], (e) => e.facet($).defaultKeymap ? [Xg] : [])), Qg = class {
	constructor(e, t, n) {
		this.from = e, this.to = t, this.diagnostic = n;
	}
}, $g = class e {
	constructor(e, t, n) {
		this.diagnostics = e, this.panel = t, this.selected = n;
	}
	static init(t, n, r) {
		let i = r.facet(p_).markerFilter;
		i && (t = i(t, r));
		let a = t.slice().sort((e, t) => e.from - t.from || e.to - t.to), o = new zt(), s = [], c = 0, l = r.doc.iter(), u = 0, d = r.doc.length;
		for (let e = 0;;) {
			let t = e == a.length ? null : a[e];
			if (!t && !s.length) break;
			let n, r;
			if (s.length) n = c, r = s.reduce((e, t) => Math.min(e, t.to), t && t.from > n ? t.from : 1e8);
			else {
				if (n = t.from, n > d) break;
				r = t.to, s.push(t), e++;
			}
			for (; e < a.length;) {
				let t = a[e];
				if (t.from == n && (t.to > t.from || t.to == n)) s.push(t), e++, r = Math.min(t.to, r);
				else {
					r = Math.min(t.from, r);
					break;
				}
			}
			r = Math.min(r, d);
			let i = !1;
			if (s.some((e) => e.from == n && (e.to == r || r == d)) && (i = n == r, !i && r - n < 10)) {
				let e = n - (u + l.value.length);
				e > 0 && (l.next(e), u = n);
				for (let e = n;;) {
					if (e >= r) {
						i = !0;
						break;
					}
					if (!l.lineBreak && u + l.value.length > e) break;
					e = u + l.value.length, u += l.value.length, l.next();
				}
			}
			let f = w_(s);
			if (i) o.add(n, n, B.widget({
				widget: new __(f),
				diagnostics: s.slice()
			}));
			else {
				let e = s.reduce((e, t) => t.markClass ? e + " " + t.markClass : e, "");
				o.add(n, r, B.mark({
					class: "cm-lintRange cm-lintRange-" + f + e,
					diagnostics: s.slice(),
					inclusiveEnd: s.some((e) => e.to > r)
				}));
			}
			if (c = r, c == d) break;
			for (let e = 0; e < s.length; e++) s[e].to <= c && s.splice(e--, 1);
		}
		let f = o.finish();
		return new e(f, n, e_(f));
	}
};
function e_(e, t = null, n = 0) {
	let r = null;
	return e.between(n, 1e9, (e, n, { spec: i }) => {
		if (!(t && i.diagnostics.indexOf(t) < 0)) {
			if (!r) r = new Qg(e, n, t || i.diagnostics[0]);
			else if (i.diagnostics.indexOf(r.diagnostic) < 0) return !1;
			else r = new Qg(r.from, n, r.diagnostic);
		}
	}), r;
}
function t_(e, t) {
	let n = t.pos, r = t.end || n, i = e.state.facet(p_).hideOn(e, n, r);
	if (i != null) return i;
	let a = e.startState.doc.lineAt(t.pos);
	return !!(e.effects.some((e) => e.is(r_)) || e.changes.touchesRange(a.from, Math.max(a.to, r)));
}
function n_(e, t) {
	return e.field(o_, !1) ? t : t.concat(A.appendConfig.of(E_));
}
var r_ = /*@__PURE__*/ A.define(), i_ = /*@__PURE__*/ A.define(), a_ = /*@__PURE__*/ A.define(), o_ = /*@__PURE__*/ k.define({
	create() {
		return new $g(B.none, null, null);
	},
	update(e, t) {
		if (t.docChanged && e.diagnostics.size) {
			let n = e.diagnostics.map(t.changes), r = null, i = e.panel;
			if (e.selected) {
				let i = t.changes.mapPos(e.selected.from, 1);
				r = e_(n, e.selected.diagnostic, i) || e_(n, null, i);
			}
			!n.size && i && t.state.facet(p_).autoPanel && (i = null), e = new $g(n, i, r);
		}
		for (let n of t.effects) if (n.is(r_)) {
			let r = t.state.facet(p_).autoPanel ? n.value.length ? y_.open : null : e.panel;
			e = $g.init(n.value, r, t.state);
		} else n.is(i_) ? e = new $g(e.diagnostics, n.value ? y_.open : null, e.selected) : n.is(a_) && (e = new $g(e.diagnostics, e.panel, n.value));
		return e;
	},
	provide: (e) => [Kc.from(e, (e) => e.panel), J.decorations.from(e, (e) => e.diagnostics)]
}), s_ = /*@__PURE__*/ B.mark({ class: "cm-lintRange cm-lintRange-active" });
function c_(e, t, n) {
	let { diagnostics: r } = e.state.field(o_), i, a = -1, o = -1;
	r.between(t - +(n < 0), t + +(n > 0), (e, r, { spec: s }) => {
		if (t >= e && t <= r && (e == r || (t > e || n > 0) && (t < r || n < 0))) return i = s.diagnostics, a = e, o = r, !1;
	});
	let s = e.state.facet(p_).tooltipFilter;
	return i && s && (i = s(i, e.state)), i ? {
		pos: a,
		end: o,
		above: !0,
		create() {
			return { dom: l_(e, i) };
		}
	} : null;
}
function l_(e, t) {
	return I("ul", { class: "cm-tooltip-lint" }, t.map((t) => g_(e, t, !1)));
}
var u_ = (e) => {
	let t = e.state.field(o_, !1);
	(!t || !t.panel) && e.dispatch({ effects: n_(e.state, [i_.of(!0)]) });
	let n = Hc(e, y_.open);
	return n && n.dom.querySelector(".cm-panel-lint ul").focus(), !0;
}, d_ = (e) => {
	let t = e.state.field(o_, !1);
	return !t || !t.panel ? !1 : (e.dispatch({ effects: i_.of(!1) }), !0);
}, f_ = [{
	key: "Mod-Shift-m",
	run: u_,
	preventDefault: !0
}, {
	key: "F8",
	run: (e) => {
		let t = e.state.field(o_, !1);
		if (!t) return !1;
		let n = e.state.selection.main, r = e_(t.diagnostics, null, n.to + 1);
		return !r && (r = e_(t.diagnostics, null, 0), !r || r.from == n.from && r.to == n.to) ? !1 : (e.dispatch({
			selection: {
				anchor: r.from,
				head: r.to
			},
			scrollIntoView: !0
		}), Rc(e, r.from, 1, {
			tooltip: T_,
			until: (e) => e.docChanged || e.newSelection.main.head < r.from || e.newSelection.main.head > r.to
		}), !0);
	}
}], p_ = /*@__PURE__*/ O.define({ combine(e) {
	return vn({ sources: e.map((e) => e.source).filter((e) => e != null) }, Mt(e.map((e) => e.config), {
		delay: 750,
		markerFilter: null,
		tooltipFilter: null,
		needsRefresh: null,
		hideOn: () => null
	}, {
		delay: Math.max,
		markerFilter: m_,
		tooltipFilter: m_,
		needsRefresh: (e, t) => e ? t ? (n) => e(n) || t(n) : e : t,
		hideOn: (e, t) => e ? t ? (n, r, i) => e(n, r, i) || t(n, r, i) : e : t,
		autoPanel: (e, t) => e || t
	}));
} });
function m_(e, t) {
	return e ? t ? (n, r) => t(e(n, r), r) : e : t;
}
function h_(e) {
	let t = [];
	if (e) actions: for (let { name: n } of e) {
		for (let e = 0; e < n.length; e++) {
			let r = n[e];
			if (/[a-zA-Z]/.test(r) && !t.some((e) => e.toLowerCase() == r.toLowerCase())) {
				t.push(r);
				continue actions;
			}
		}
		t.push("");
	}
	return t;
}
function g_(e, t, n) {
	var r;
	let i = n ? h_(t.actions) : [];
	return I("li", { class: "cm-diagnostic cm-diagnostic-" + t.severity }, I("span", { class: "cm-diagnosticText" }, t.renderMessage ? t.renderMessage(e) : t.message), (r = t.actions) == null ? void 0 : r.map((n, r) => {
		let a = !1, o = (r) => {
			if (r.preventDefault(), a) return;
			a = !0;
			let i = e_(e.state.field(o_).diagnostics, t);
			i && n.apply(e, i.from, i.to);
		}, { name: s } = n, c = i[r] ? s.indexOf(i[r]) : -1, l = c < 0 ? s : [
			s.slice(0, c),
			I("u", s.slice(c, c + 1)),
			s.slice(c + 1)
		];
		return I("button", {
			type: "button",
			class: "cm-diagnosticAction" + (n.markClass ? " " + n.markClass : ""),
			onclick: o,
			onmousedown: o,
			"aria-label": ` Action: ${s}${c < 0 ? "" : ` (access key "${i[r]})"`}.`
		}, l);
	}), t.source && I("div", { class: "cm-diagnosticSource" }, t.source));
}
var __ = class extends Fn {
	constructor(e) {
		super(), this.sev = e;
	}
	eq(e) {
		return e.sev == this.sev;
	}
	toDOM() {
		return I("span", { class: "cm-lintPoint cm-lintPoint-" + this.sev });
	}
}, v_ = class {
	constructor(e, t) {
		this.diagnostic = t, this.id = "item_" + Math.floor(Math.random() * 4294967295).toString(16), this.dom = g_(e, t, !0), this.dom.id = this.id, this.dom.setAttribute("role", "option");
	}
}, y_ = class e {
	constructor(e) {
		this.view = e, this.items = [];
		let t = (t) => {
			if (!(t.ctrlKey || t.altKey || t.metaKey)) {
				if (t.keyCode == 27) d_(this.view), this.view.focus();
				else if (t.keyCode == 38 || t.keyCode == 33) this.moveSelection((this.selectedIndex - 1 + this.items.length) % this.items.length);
				else if (t.keyCode == 40 || t.keyCode == 34) this.moveSelection((this.selectedIndex + 1) % this.items.length);
				else if (t.keyCode == 36) this.moveSelection(0);
				else if (t.keyCode == 35) this.moveSelection(this.items.length - 1);
				else if (t.keyCode == 13) this.view.focus();
				else if (t.keyCode >= 65 && t.keyCode <= 90 && this.selectedIndex >= 0) {
					let { diagnostic: n } = this.items[this.selectedIndex], r = h_(n.actions);
					for (let i = 0; i < r.length; i++) if (r[i].toUpperCase().charCodeAt(0) == t.keyCode) {
						let t = e_(this.view.state.field(o_).diagnostics, n);
						t && n.actions[i].apply(e, t.from, t.to);
					}
				} else return;
				t.preventDefault();
			}
		}, n = (e) => {
			for (let t = 0; t < this.items.length; t++) this.items[t].dom.contains(e.target) && this.moveSelection(t);
		};
		this.list = I("ul", {
			tabIndex: 0,
			role: "listbox",
			"aria-label": this.view.state.phrase("Diagnostics"),
			onkeydown: t,
			onclick: n
		}), this.dom = I("div", { class: "cm-panel-lint" }, this.list, I("button", {
			type: "button",
			name: "close",
			"aria-label": this.view.state.phrase("close"),
			onclick: () => d_(this.view)
		}, "×")), this.update();
	}
	get selectedIndex() {
		let e = this.view.state.field(o_).selected;
		if (!e) return -1;
		for (let t = 0; t < this.items.length; t++) if (this.items[t].diagnostic == e.diagnostic) return t;
		return -1;
	}
	update() {
		let { diagnostics: e, selected: t } = this.view.state.field(o_), n = 0, r = !1, i = null, a = /* @__PURE__ */ new Set();
		for (e.between(0, this.view.state.doc.length, (e, o, { spec: s }) => {
			for (let e of s.diagnostics) {
				if (a.has(e)) continue;
				a.add(e);
				let o = -1, s;
				for (let t = n; t < this.items.length; t++) if (this.items[t].diagnostic == e) {
					o = t;
					break;
				}
				o < 0 ? (s = new v_(this.view, e), this.items.splice(n, 0, s), r = !0) : (s = this.items[o], o > n && (this.items.splice(n, o - n), r = !0)), t && s.diagnostic == t.diagnostic ? s.dom.hasAttribute("aria-selected") || (s.dom.setAttribute("aria-selected", "true"), i = s) : s.dom.hasAttribute("aria-selected") && s.dom.removeAttribute("aria-selected"), n++;
			}
		}); n < this.items.length && !(this.items.length == 1 && this.items[0].diagnostic.from < 0);) r = !0, this.items.pop();
		this.items.length == 0 && (this.items.push(new v_(this.view, {
			from: -1,
			to: -1,
			severity: "info",
			message: this.view.state.phrase("No diagnostics")
		})), r = !0), i ? (this.list.setAttribute("aria-activedescendant", i.id), this.view.requestMeasure({
			key: this,
			read: () => ({
				sel: i.dom.getBoundingClientRect(),
				panel: this.list.getBoundingClientRect()
			}),
			write: ({ sel: e, panel: t }) => {
				let n = t.height / this.list.offsetHeight;
				e.top < t.top ? this.list.scrollTop -= (t.top - e.top) / n : e.bottom > t.bottom && (this.list.scrollTop += (e.bottom - t.bottom) / n);
			}
		})) : this.selectedIndex < 0 && this.list.removeAttribute("aria-activedescendant"), r && this.sync();
	}
	sync() {
		let e = this.list.firstChild;
		function t() {
			let t = e;
			e = t.nextSibling, t.remove();
		}
		for (let n of this.items) if (n.dom.parentNode == this.list) {
			for (; e != n.dom;) t();
			e = n.dom.nextSibling;
		} else this.list.insertBefore(n.dom, e);
		for (; e;) t();
	}
	moveSelection(e) {
		if (this.selectedIndex < 0) return;
		let t = e_(this.view.state.field(o_).diagnostics, this.items[e].diagnostic);
		t && this.view.dispatch({
			selection: {
				anchor: t.from,
				head: t.to
			},
			scrollIntoView: !0,
			effects: a_.of(t)
		});
	}
	static open(t) {
		return new e(t);
	}
};
function b_(e, t = "viewBox=\"0 0 40 40\"") {
	return `url('data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" ${t}>${encodeURIComponent(e)}</svg>')`;
}
function x_(e) {
	return b_(`<path d="m0 2.5 l2 -1.5 l1 0 l2 1.5 l1 0" stroke="${e}" fill="none" stroke-width=".7"/>`, "width=\"6\" height=\"3\"");
}
var S_ = /*@__PURE__*/ J.baseTheme({
	".cm-diagnostic": {
		padding: "3px 6px 3px 8px",
		marginLeft: "-1px",
		display: "block",
		whiteSpace: "pre-wrap"
	},
	".cm-diagnostic-error": { borderLeft: "5px solid #d11" },
	".cm-diagnostic-warning": { borderLeft: "5px solid orange" },
	".cm-diagnostic-info": { borderLeft: "5px solid #999" },
	".cm-diagnostic-hint": { borderLeft: "5px solid #66d" },
	".cm-diagnosticAction": {
		font: "inherit",
		border: "none",
		padding: "2px 4px",
		backgroundColor: "#444",
		color: "white",
		borderRadius: "3px",
		marginLeft: "8px",
		cursor: "pointer"
	},
	".cm-diagnosticSource": {
		fontSize: "70%",
		opacity: .7
	},
	".cm-lintRange": {
		backgroundPosition: "left bottom",
		backgroundRepeat: "repeat-x",
		paddingBottom: "0.7px"
	},
	".cm-lintRange-error": { backgroundImage: /*@__PURE__*/ x_("#f11") },
	".cm-lintRange-warning": { backgroundImage: /*@__PURE__*/ x_("orange") },
	".cm-lintRange-info": { backgroundImage: /*@__PURE__*/ x_("#999") },
	".cm-lintRange-hint": { backgroundImage: /*@__PURE__*/ x_("#66d") },
	".cm-lintRange-active": { backgroundColor: "#ffdd9980" },
	".cm-tooltip-lint": {
		padding: 0,
		margin: 0
	},
	".cm-lintPoint": {
		position: "relative",
		"&:after": {
			content: "\"\"",
			position: "absolute",
			bottom: 0,
			left: "-2px",
			borderLeft: "3px solid transparent",
			borderRight: "3px solid transparent",
			borderBottom: "4px solid #d11"
		}
	},
	".cm-lintPoint-warning": { "&:after": { borderBottomColor: "orange" } },
	".cm-lintPoint-info": { "&:after": { borderBottomColor: "#999" } },
	".cm-lintPoint-hint": { "&:after": { borderBottomColor: "#66d" } },
	".cm-panel.cm-panel-lint": {
		position: "relative",
		"& ul": {
			maxHeight: "100px",
			overflowY: "auto",
			"& [aria-selected]": {
				backgroundColor: "#ddd",
				"& u": { textDecoration: "underline" }
			},
			"&:focus [aria-selected]": {
				background_fallback: "#bdf",
				backgroundColor: "Highlight",
				color_fallback: "white",
				color: "HighlightText"
			},
			"& u": { textDecoration: "none" },
			padding: 0,
			margin: 0
		},
		"& [name=close]": {
			position: "absolute",
			top: "0",
			right: "2px",
			background: "inherit",
			border: "none",
			font: "inherit",
			padding: 0,
			margin: 0
		}
	},
	"&dark .cm-lintRange-active": { backgroundColor: "#86714a80" },
	"&dark .cm-panel.cm-panel-lint ul": { "& [aria-selected]": { backgroundColor: "#2e343e" } }
});
function C_(e) {
	return e == "error" ? 4 : e == "warning" ? 3 : e == "info" ? 2 : 1;
}
function w_(e) {
	let t = "hint", n = 1;
	for (let r of e) {
		let e = C_(r.severity);
		e > n && (n = e, t = r.severity);
	}
	return t;
}
var T_ = /*@__PURE__*/ Lc(c_, { hideOn: t_ }), E_ = [
	o_,
	/*@__PURE__*/ J.decorations.compute([o_], (e) => {
		let { selected: t, panel: n } = e.field(o_);
		return !t || !n || t.from == t.to ? B.none : B.set([s_.range(t.from, t.to)]);
	}),
	T_,
	S_
], D_ = [
	yl(),
	Cl(),
	ec(),
	mf(),
	rd(),
	Ps(),
	Ws(),
	N.allowMultipleSelections.of(!0),
	Au(),
	ld(fd, { fallback: !0 }),
	Sd(),
	Mg(),
	Yg(),
	hc(),
	vc(),
	sc(),
	Pm(),
	gs.of([
		...Rg,
		...bm,
		...Ch,
		...Nf,
		...Ju,
		...Xg,
		...f_
	])
], O_ = Pd.define({
	startState() {
		return { inComment: !1 };
	},
	token(e, t) {
		return t.inComment ? (e.skipTo("*/") ? (e.next(), e.next(), t.inComment = !1) : e.skipToEnd(), "comment") : e.match(/\/\*/) ? (t.inComment = !0, "comment") : e.match(/\/\/.*/) ? "comment" : e.match(/"(?:[^\\]|\\.)*?(?:"|$)/) ? "string" : e.match(/\b(?:all|and|any|ascii|at|base64|base64wide|condition|contains|entrypoint|filesize|for|fullword|global|import|in|include|int8|int16|int32|int8be|int16be|int32be|matches|meta|nocase|not|or|of|private|rule|strings|them|uint8|uint16|uint32|uint8be|uint16be|uint32be|wide|xor)\b/) ? "keyword" : e.match(/\b(?:true|false)\b/) ? "atom" : e.match(/0x[a-f\d]+|(?:\.\d+|\d+\.?\d*)/i) || e.match(/(\{(?:[\s])*(?:[a-fA-F\d?]{2}\s?)+(?:[\s])*\})/) ? "number" : e.match(/[-+/*=<>:]+/) ? "operator" : e.match(/\{/) || e.match(/\}/) ? "bracket" : e.match(/\$\w*/) ? "labelName" : (e.next(), null);
	},
	languageData: { commentTokens: {
		line: "//",
		block: {
			open: "/*",
			close: "*/"
		}
	} }
}), k_ = J.theme({
	"&": { height: "300px" },
	".cm-scroller": { overflow: "auto" }
});
function A_(e, t = {}) {
	let n = document.createElement("div");
	e.parentNode.appendChild(n), e.style.display = "none";
	let r = e.value;
	t.placeholder && r.length == 0 && (r = t.placeholder);
	let i = !1;
	(!t.textarea_no_sync || t.textarea_no_sync !== !1) && (i = J.updateListener.of(function(t) {
		t.docChanged && (e.value = t.state.doc.toString());
	}));
	let a = [
		D_,
		i || [],
		k_,
		O_,
		...t.codemirror_extensions || []
	], o = new J({
		state: N.create({
			doc: r,
			extensions: a
		}),
		parent: n
	});
	return !t.textarea_no_sync || t.textarea_no_sync, o;
}
//#endregion
export { A_ as createYaraEditor };
