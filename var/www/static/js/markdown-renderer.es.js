//#region node_modules/dompurify/dist/purify.es.mjs
function e(e, t) {
	(t == null || t > e.length) && (t = e.length);
	for (var n = 0, r = Array(t); n < t; n++) r[n] = e[n];
	return r;
}
function t(e) {
	if (Array.isArray(e)) return e;
}
function n(e, t) {
	var n = e == null ? null : typeof Symbol < "u" && e[Symbol.iterator] || e["@@iterator"];
	if (n != null) {
		var r, i, a, o, s = [], c = !0, l = !1;
		try {
			if (a = (n = n.call(e)).next, t !== 0) for (; !(c = (r = a.call(n)).done) && (s.push(r.value), s.length !== t); c = !0);
		} catch (e) {
			l = !0, i = e;
		} finally {
			try {
				if (!c && n.return != null && (o = n.return(), Object(o) !== o)) return;
			} finally {
				if (l) throw i;
			}
		}
		return s;
	}
}
function r() {
	throw TypeError("Invalid attempt to destructure non-iterable instance.\nIn order to be iterable, non-array objects must have a [Symbol.iterator]() method.");
}
function i(e, i) {
	return t(e) || n(e, i) || a(e, i) || r();
}
function a(t, n) {
	if (t) {
		if (typeof t == "string") return e(t, n);
		var r = {}.toString.call(t).slice(8, -1);
		return r === "Object" && t.constructor && (r = t.constructor.name), r === "Map" || r === "Set" ? Array.from(t) : r === "Arguments" || /^(?:Ui|I)nt(?:8|16|32)(?:Clamped)?Array$/.test(r) ? e(t, n) : void 0;
	}
}
var o = Object.entries, s = Object.setPrototypeOf, c = Object.isFrozen, l = Object.getPrototypeOf, u = Object.getOwnPropertyDescriptor, d = Object.freeze, f = Object.seal, p = Object.create, m = typeof Reflect < "u" && Reflect, h = m.apply, ee = m.construct;
d || (d = function(e) {
	return e;
}), f || (f = function(e) {
	return e;
}), h || (h = function(e, t) {
	var n = [...arguments].slice(2);
	return e.apply(t, n);
}), ee || (ee = function(e) {
	return new e(...[...arguments].slice(1));
});
var te = y(Array.prototype.forEach), ne = y(Array.prototype.lastIndexOf), re = y(Array.prototype.pop), ie = y(Array.prototype.push), ae = y(Array.prototype.splice), oe = Array.isArray, se = y(String.prototype.toLowerCase), ce = y(String.prototype.toString), le = y(String.prototype.match), ue = y(String.prototype.replace), de = y(String.prototype.indexOf), fe = y(String.prototype.trim), pe = y(Number.prototype.toString), me = y(Boolean.prototype.toString), he = typeof BigInt > "u" ? null : y(BigInt.prototype.toString), g = typeof Symbol > "u" ? null : y(Symbol.prototype.toString), _ = y(Object.prototype.hasOwnProperty), ge = y(Object.prototype.toString), v = y(RegExp.prototype.test), _e = b(TypeError);
function y(e) {
	return function(t) {
		t instanceof RegExp && (t.lastIndex = 0);
		var n = [...arguments].slice(1);
		return h(e, t, n);
	};
}
function b(e) {
	return function() {
		return ee(e, [...arguments]);
	};
}
function x(e, t) {
	let n = arguments.length > 2 && arguments[2] !== void 0 ? arguments[2] : se;
	if (s && s(e, null), !oe(t)) return e;
	let r = t.length;
	for (; r--;) {
		let i = t[r];
		if (typeof i == "string") {
			let e = n(i);
			e !== i && (c(t) || (t[r] = e), i = e);
		}
		e[i] = !0;
	}
	return e;
}
function ve(e) {
	for (let t = 0; t < e.length; t++) _(e, t) || (e[t] = null);
	return e;
}
function S(e) {
	let t = p(null);
	for (let r of o(e)) {
		var n = i(r, 2);
		let a = n[0], o = n[1];
		_(e, a) && (t[a] = oe(o) ? ve(o) : o && typeof o == "object" && o.constructor === Object ? S(o) : o);
	}
	return t;
}
function ye(e) {
	switch (typeof e) {
		case "string": return e;
		case "number": return pe(e);
		case "boolean": return me(e);
		case "bigint": return he ? he(e) : "0";
		case "symbol": return g ? g(e) : "Symbol()";
		case "undefined": return ge(e);
		case "function":
		case "object": {
			if (e === null) return ge(e);
			let t = e, n = C(t, "toString");
			if (typeof n == "function") {
				let e = n(t);
				return typeof e == "string" ? e : ge(e);
			}
			return ge(e);
		}
		default: return ge(e);
	}
}
function C(e, t) {
	for (; e !== null;) {
		let n = u(e, t);
		if (n) {
			if (n.get) return y(n.get);
			if (typeof n.value == "function") return y(n.value);
		}
		e = l(e);
	}
	function n() {
		return null;
	}
	return n;
}
function be(e) {
	try {
		return v(e, ""), !0;
	} catch (e) {
		return !1;
	}
}
var xe = d(/* @__PURE__ */ "a.abbr.acronym.address.area.article.aside.audio.b.bdi.bdo.big.blink.blockquote.body.br.button.canvas.caption.center.cite.code.col.colgroup.content.data.datalist.dd.decorator.del.details.dfn.dialog.dir.div.dl.dt.element.em.fieldset.figcaption.figure.font.footer.form.h1.h2.h3.h4.h5.h6.head.header.hgroup.hr.html.i.img.input.ins.kbd.label.legend.li.main.map.mark.marquee.menu.menuitem.meter.nav.nobr.ol.optgroup.option.output.p.picture.pre.progress.q.rp.rt.ruby.s.samp.search.section.select.shadow.slot.small.source.spacer.span.strike.strong.style.sub.summary.sup.table.tbody.td.template.textarea.tfoot.th.thead.time.tr.track.tt.u.ul.var.video.wbr".split(".")), Se = d(/* @__PURE__ */ "svg.a.altglyph.altglyphdef.altglyphitem.animatecolor.animatemotion.animatetransform.circle.clippath.defs.desc.ellipse.enterkeyhint.exportparts.filter.font.g.glyph.glyphref.hkern.image.inputmode.line.lineargradient.marker.mask.metadata.mpath.part.path.pattern.polygon.polyline.radialgradient.rect.stop.style.switch.symbol.text.textpath.title.tref.tspan.view.vkern".split(".")), Ce = d([
	"feBlend",
	"feColorMatrix",
	"feComponentTransfer",
	"feComposite",
	"feConvolveMatrix",
	"feDiffuseLighting",
	"feDisplacementMap",
	"feDistantLight",
	"feDropShadow",
	"feFlood",
	"feFuncA",
	"feFuncB",
	"feFuncG",
	"feFuncR",
	"feGaussianBlur",
	"feImage",
	"feMerge",
	"feMergeNode",
	"feMorphology",
	"feOffset",
	"fePointLight",
	"feSpecularLighting",
	"feSpotLight",
	"feTile",
	"feTurbulence"
]), we = d([
	"animate",
	"color-profile",
	"cursor",
	"discard",
	"font-face",
	"font-face-format",
	"font-face-name",
	"font-face-src",
	"font-face-uri",
	"foreignobject",
	"hatch",
	"hatchpath",
	"mesh",
	"meshgradient",
	"meshpatch",
	"meshrow",
	"missing-glyph",
	"script",
	"set",
	"solidcolor",
	"unknown",
	"use"
]), Te = d(/* @__PURE__ */ "math.menclose.merror.mfenced.mfrac.mglyph.mi.mlabeledtr.mmultiscripts.mn.mo.mover.mpadded.mphantom.mroot.mrow.ms.mspace.msqrt.mstyle.msub.msup.msubsup.mtable.mtd.mtext.mtr.munder.munderover.mprescripts".split(".")), Ee = d([
	"maction",
	"maligngroup",
	"malignmark",
	"mlongdiv",
	"mscarries",
	"mscarry",
	"msgroup",
	"mstack",
	"msline",
	"msrow",
	"semantics",
	"annotation",
	"annotation-xml",
	"mprescripts",
	"none"
]), De = d(["#text"]), Oe = d(/* @__PURE__ */ "accept.action.align.alt.autocapitalize.autocomplete.autopictureinpicture.autoplay.background.bgcolor.border.capture.cellpadding.cellspacing.checked.cite.class.clear.color.cols.colspan.command.commandfor.controls.controlslist.coords.crossorigin.datetime.decoding.default.dir.disabled.disablepictureinpicture.disableremoteplayback.download.draggable.enctype.enterkeyhint.exportparts.face.for.headers.height.hidden.high.href.hreflang.id.inert.inputmode.integrity.ismap.kind.label.lang.list.loading.loop.low.max.maxlength.media.method.min.minlength.multiple.muted.name.nonce.noshade.novalidate.nowrap.open.optimum.part.pattern.placeholder.playsinline.popover.popovertarget.popovertargetaction.poster.preload.pubdate.radiogroup.readonly.rel.required.rev.reversed.role.rows.rowspan.spellcheck.scope.selected.shape.size.sizes.slot.span.srclang.start.src.srcset.step.style.summary.tabindex.title.translate.type.usemap.valign.value.width.wrap.xmlns".split(".")), ke = d(/* @__PURE__ */ "accent-height.accumulate.additive.alignment-baseline.amplitude.ascent.attributename.attributetype.azimuth.basefrequency.baseline-shift.begin.bias.by.class.clip.clippathunits.clip-path.clip-rule.color.color-interpolation.color-interpolation-filters.color-profile.color-rendering.cx.cy.d.dx.dy.diffuseconstant.direction.display.divisor.dominant-baseline.dur.edgemode.elevation.end.exponent.fill.fill-opacity.fill-rule.filter.filterunits.flood-color.flood-opacity.font-family.font-size.font-size-adjust.font-stretch.font-style.font-variant.font-weight.fx.fy.g1.g2.glyph-name.glyphref.gradientunits.gradienttransform.height.href.id.image-rendering.in.in2.intercept.k.k1.k2.k3.k4.kerning.keypoints.keysplines.keytimes.lang.lengthadjust.letter-spacing.kernelmatrix.kernelunitlength.lighting-color.local.marker-end.marker-mid.marker-start.markerheight.markerunits.markerwidth.maskcontentunits.maskunits.max.mask.mask-type.media.method.mode.min.name.numoctaves.offset.operator.opacity.order.orient.orientation.origin.overflow.paint-order.path.pathlength.patterncontentunits.patterntransform.patternunits.pointer-events.points.preservealpha.preserveaspectratio.primitiveunits.r.rx.ry.radius.refx.refy.repeatcount.repeatdur.restart.result.rotate.scale.seed.shape-rendering.slope.specularconstant.specularexponent.spreadmethod.startoffset.stddeviation.stitchtiles.stop-color.stop-opacity.stroke-dasharray.stroke-dashoffset.stroke-linecap.stroke-linejoin.stroke-miterlimit.stroke-opacity.stroke.stroke-width.style.surfacescale.systemlanguage.tabindex.tablevalues.targetx.targety.transform.transform-origin.text-anchor.text-decoration.text-orientation.text-rendering.textlength.type.u1.u2.unicode.values.vector-effect.viewbox.visibility.version.vert-adv-y.vert-origin-x.vert-origin-y.width.word-spacing.wrap.writing-mode.xchannelselector.ychannelselector.x.x1.x2.xmlns.y.y1.y2.z.zoomandpan".split(".")), Ae = d(/* @__PURE__ */ "accent.accentunder.align.bevelled.close.columnalign.columnlines.columnspacing.columnspan.denomalign.depth.dir.display.displaystyle.encoding.fence.frame.height.href.id.largeop.length.linethickness.lquote.lspace.mathbackground.mathcolor.mathsize.mathvariant.maxsize.minsize.movablelimits.notation.numalign.open.rowalign.rowlines.rowspacing.rowspan.rspace.rquote.scriptlevel.scriptminsize.scriptsizemultiplier.selection.separator.separators.stretchy.subscriptshift.supscriptshift.symmetric.voffset.width.xmlns".split(".")), je = d([
	"xlink:href",
	"xml:id",
	"xlink:title",
	"xml:space",
	"xmlns:xlink"
]), Me = f(/{{[\w\W]*|^[\w\W]*}}/g), Ne = f(/<%[\w\W]*|^[\w\W]*%>/g), Pe = f(/\${[\w\W]*/g), Fe = f(/^data-[\-\w.\u00B7-\uFFFF]+$/), Ie = f(/^aria-[\-\w]+$/), Le = f(/^(?:(?:(?:f|ht)tps?|mailto|tel|callto|sms|cid|xmpp|matrix):|[^a-z]|[a-z+.\-]+(?:[^a-z+.\-:]|$))/i), Re = f(/^(?:\w+script|data):/i), ze = f(/[\u0000-\u0020\u00A0\u1680\u180E\u2000-\u2029\u205F\u3000]/g), Be = f(/^html$/i), Ve = f(/^[a-z][.\w]*(-[.\w]+)+$/i), He = f(/<[/\w!]/g), Ue = f(/<[/\w]/g), We = f(/<\/no(script|embed|frames)/i), Ge = f(/\/>/i), w = {
	element: 1,
	attribute: 2,
	text: 3,
	cdataSection: 4,
	entityReference: 5,
	entityNode: 6,
	processingInstruction: 7,
	comment: 8,
	document: 9,
	documentType: 10,
	documentFragment: 11,
	notation: 12
}, Ke = [
	"style",
	"script",
	"xmp",
	"iframe",
	"noembed",
	"noframes",
	"plaintext",
	"noscript"
], qe = d(x({}, Ke)), Je = function() {
	let e = {};
	return te(Ke, (t) => {
		e[t] = f(RegExp("</" + t + "(?=[\\t\\n\\f\\r />])", "i"));
	}), d(e);
}(), Ye = function() {
	return typeof window > "u" ? null : window;
}, Xe = function(e, t) {
	if (typeof e != "object" || typeof e.createPolicy != "function") return null;
	let n = null, r = "data-tt-policy-suffix";
	t && t.hasAttribute(r) && (n = t.getAttribute(r));
	let i = "dompurify" + (n ? "#" + n : "");
	try {
		return e.createPolicy(i, {
			createHTML(e) {
				return e;
			},
			createScriptURL(e) {
				return e;
			}
		});
	} catch (e) {
		return console.warn("TrustedTypes policy " + i + " could not be created."), null;
	}
}, Ze = function() {
	return {
		afterSanitizeAttributes: [],
		afterSanitizeElements: [],
		afterSanitizeShadowDOM: [],
		beforeSanitizeAttributes: [],
		beforeSanitizeElements: [],
		beforeSanitizeShadowDOM: [],
		uponSanitizeAttribute: [],
		uponSanitizeElement: [],
		uponSanitizeShadowNode: []
	};
}, T = function(e, t, n, r) {
	return _(e, t) && oe(e[t]) ? x(r.base ? S(r.base) : {}, e[t], r.transform) : n;
}, Qe = function(e, t, n) {
	let r = _(e, t) ? e[t] : void 0;
	return r && typeof r == "object" ? S(r) : n();
};
function $e() {
	let e = arguments.length > 0 && arguments[0] !== void 0 ? arguments[0] : Ye(), t = (e) => $e(e);
	if (t.version = "3.4.14", t.removed = [], !e || !e.document || e.document.nodeType !== w.document || !e.Element) return t.isSupported = !1, t;
	let n = e.document, r = n, i = r.currentScript;
	e.DocumentFragment;
	let a = e.HTMLTemplateElement, s = e.Node, c = e.Element, l = e.NodeFilter;
	e.NamedNodeMap === void 0 && (e.NamedNodeMap || e.MozNamedAttrMap), e.HTMLFormElement;
	let u = e.DOMParser, m = e.trustedTypes, h = c.prototype, ee = C(h, "cloneNode"), pe = C(h, "remove"), me = C(h, "nextSibling"), he = C(h, "childNodes"), g = C(h, "parentNode"), ge = C(h, "shadowRoot"), y = C(h, "attributes"), b = s && s.prototype ? C(s.prototype, "nodeType") : null, ve = s && s.prototype ? C(s.prototype, "nodeName") : null, Ke = s && s.prototype ? C(s.prototype, "ownerDocument") : null, et = function(e) {
		return b ? b(e) : e.nodeType;
	}, tt = function(e) {
		return ve ? ve(e) : e.nodeName;
	};
	if (typeof a == "function") {
		let e = n.createElement("template");
		e.content && e.content.ownerDocument && (n = e.content.ownerDocument);
	}
	let E, nt = "", D, rt = !1, O = 0, it = function() {
		if (O > 0) throw _e("A configured TRUSTED_TYPES_POLICY callback (createHTML or createScriptURL) must not call DOMPurify.sanitize, as that causes infinite recursion. Do not pass a policy whose callbacks wrap DOMPurify as TRUSTED_TYPES_POLICY; see the \"DOMPurify and Trusted Types\" section of the README.");
	}, k = function(e) {
		it(), O++;
		try {
			return E.createHTML(e);
		} finally {
			O--;
		}
	}, at = function(e) {
		it(), O++;
		try {
			return E.createScriptURL(e);
		} finally {
			O--;
		}
	}, ot = function() {
		return rt || (D = Xe(m, i), rt = !0), D;
	}, A = n, st = A.implementation, j = A.createNodeIterator, ct = A.createDocumentFragment, M = A.getElementsByTagName, lt = r.importNode, N = Ze();
	t.isSupported = typeof o == "function" && typeof g == "function" && st && st.createHTMLDocument !== void 0;
	let ut = Me, dt = Ne, ft = Pe, pt = Fe, mt = Ie, ht = Re, gt = ze, _t = Ve, vt = Le, P = null, yt = x({}, [
		...xe,
		...Se,
		...Ce,
		...Te,
		...De
	]), F = null, bt = x({}, [
		...Oe,
		...ke,
		...Ae,
		...je
	]), I = Object.seal(p(null, {
		tagNameCheck: {
			writable: !0,
			configurable: !1,
			enumerable: !0,
			value: null
		},
		attributeNameCheck: {
			writable: !0,
			configurable: !1,
			enumerable: !0,
			value: null
		},
		allowCustomizedBuiltInElements: {
			writable: !0,
			configurable: !1,
			enumerable: !0,
			value: !1
		}
	})), L = null, xt = null, R = Object.seal(p(null, {
		tagCheck: {
			writable: !0,
			configurable: !1,
			enumerable: !0,
			value: null
		},
		attributeCheck: {
			writable: !0,
			configurable: !1,
			enumerable: !0,
			value: null
		}
	})), St = !0, Ct = !0, wt = !1, Tt = !0, z = !1, Et = !0, Dt = !1, Ot = !1, kt = null, At = null, jt = !1, B = !1, V = !1, H = !1, Mt = !0, Nt = !1, Pt = "user-content-", Ft = !0, It = !1, Lt = {}, Rt = null, zt = x({}, /* @__PURE__ */ "annotation-xml.audio.colgroup.desc.foreignobject.head.iframe.math.mi.mn.mo.ms.mtext.noembed.noframes.noscript.plaintext.script.selectedcontent.style.svg.template.thead.title.video.xmp".split(".")), Bt = null, Vt = x({}, [
		"audio",
		"video",
		"img",
		"source",
		"image",
		"track"
	]), Ht = null, Ut = x({}, [
		"alt",
		"class",
		"for",
		"id",
		"label",
		"name",
		"pattern",
		"placeholder",
		"role",
		"summary",
		"title",
		"value",
		"style",
		"xmlns"
	]), Wt = "http://www.w3.org/1998/Math/MathML", Gt = "http://www.w3.org/2000/svg", U = "http://www.w3.org/1999/xhtml", Kt = U, qt = !1, Jt = null, Yt = x({}, [
		Wt,
		Gt,
		U
	], ce), Xt = d([
		"mi",
		"mo",
		"mn",
		"ms",
		"mtext"
	]), Zt = x({}, Xt), Qt = d(["annotation-xml"]), $t = x({}, Qt), en = x({}, [
		"title",
		"style",
		"font",
		"a",
		"script"
	]), tn = null, nn = ["application/xhtml+xml", "text/html"], W = null, rn = null, an = n.createElement("form"), on = function(e) {
		return e instanceof RegExp || e instanceof Function;
	}, sn = function() {
		let e = arguments.length > 0 && arguments[0] !== void 0 ? arguments[0] : {};
		if (rn && rn === e) return;
		(!e || typeof e != "object") && (e = {}), e = S(e), tn = nn.indexOf(e.PARSER_MEDIA_TYPE) === -1 ? "text/html" : e.PARSER_MEDIA_TYPE, W = tn === "application/xhtml+xml" ? ce : se, P = T(e, "ALLOWED_TAGS", yt, { transform: W }), F = T(e, "ALLOWED_ATTR", bt, { transform: W }), Jt = T(e, "ALLOWED_NAMESPACES", Yt, { transform: ce }), Ht = T(e, "ADD_URI_SAFE_ATTR", Ut, {
			transform: W,
			base: Ut
		}), Bt = T(e, "ADD_DATA_URI_TAGS", Vt, {
			transform: W,
			base: Vt
		}), Rt = T(e, "FORBID_CONTENTS", zt, { transform: W }), L = T(e, "FORBID_TAGS", S({}), { transform: W }), xt = T(e, "FORBID_ATTR", S({}), { transform: W }), Lt = _(e, "USE_PROFILES") ? e.USE_PROFILES && typeof e.USE_PROFILES == "object" ? S(e.USE_PROFILES) : e.USE_PROFILES : !1, St = e.ALLOW_ARIA_ATTR !== !1, Ct = e.ALLOW_DATA_ATTR !== !1, wt = e.ALLOW_UNKNOWN_PROTOCOLS || !1, Tt = e.ALLOW_SELF_CLOSE_IN_ATTR !== !1, z = e.SAFE_FOR_TEMPLATES || !1, Et = e.SAFE_FOR_XML !== !1, Dt = e.WHOLE_DOCUMENT || !1, B = e.RETURN_DOM || !1, V = e.RETURN_DOM_FRAGMENT || !1, H = e.RETURN_TRUSTED_TYPE || !1, jt = e.FORCE_BODY || !1, Mt = e.SANITIZE_DOM !== !1, Nt = e.SANITIZE_NAMED_PROPS || !1, Ft = e.KEEP_CONTENT !== !1, It = e.IN_PLACE || !1, vt = be(e.ALLOWED_URI_REGEXP) ? e.ALLOWED_URI_REGEXP : Le, Kt = typeof e.NAMESPACE == "string" ? e.NAMESPACE : U, Zt = Qe(e, "MATHML_TEXT_INTEGRATION_POINTS", () => x({}, Xt)), $t = Qe(e, "HTML_INTEGRATION_POINTS", () => x({}, Qt));
		let t = Qe(e, "CUSTOM_ELEMENT_HANDLING", () => p(null));
		if (I = p(null), _(t, "tagNameCheck") && on(t.tagNameCheck) && (I.tagNameCheck = t.tagNameCheck), _(t, "attributeNameCheck") && on(t.attributeNameCheck) && (I.attributeNameCheck = t.attributeNameCheck), _(t, "allowCustomizedBuiltInElements") && typeof t.allowCustomizedBuiltInElements == "boolean" && (I.allowCustomizedBuiltInElements = t.allowCustomizedBuiltInElements), f(I), z && (Ct = !1), V && (B = !0), Lt && (P = x({}, De), F = p(null), Lt.html === !0 && (x(P, xe), x(F, Oe)), Lt.svg === !0 && (x(P, Se), x(F, ke), x(F, je)), Lt.svgFilters === !0 && (x(P, Ce), x(F, ke), x(F, je)), Lt.mathMl === !0 && (x(P, Te), x(F, Ae), x(F, je))), R.tagCheck = null, R.attributeCheck = null, _(e, "ADD_TAGS") && (typeof e.ADD_TAGS == "function" ? R.tagCheck = e.ADD_TAGS : oe(e.ADD_TAGS) && (P === yt && (P = S(P)), x(P, e.ADD_TAGS, W))), _(e, "ADD_ATTR") && (typeof e.ADD_ATTR == "function" ? R.attributeCheck = e.ADD_ATTR : oe(e.ADD_ATTR) && (F === bt && (F = S(F)), x(F, e.ADD_ATTR, W))), _(e, "ADD_FORBID_CONTENTS") && oe(e.ADD_FORBID_CONTENTS) && (Rt === zt && (Rt = S(Rt)), x(Rt, e.ADD_FORBID_CONTENTS, W)), Ft && (P["#text"] = !0), Dt && x(P, [
			"html",
			"head",
			"body"
		]), P.table && (x(P, ["tbody"]), delete L.tbody), e.TRUSTED_TYPES_POLICY) {
			if (typeof e.TRUSTED_TYPES_POLICY.createHTML != "function") throw _e("TRUSTED_TYPES_POLICY configuration option must provide a \"createHTML\" hook.");
			if (typeof e.TRUSTED_TYPES_POLICY.createScriptURL != "function") throw _e("TRUSTED_TYPES_POLICY configuration option must provide a \"createScriptURL\" hook.");
			let t = E;
			E = e.TRUSTED_TYPES_POLICY;
			try {
				nt = k("");
			} catch (e) {
				throw E = t, e;
			}
		} else e.TRUSTED_TYPES_POLICY === null ? (E = void 0, nt = "") : (E === void 0 && (E = ot()), E && typeof nt == "string" && (nt = k("")));
		d && d(e), rn = e;
	}, cn = x({}, [
		...Se,
		...Ce,
		...we
	]), ln = x({}, [...Te, ...Ee]), un = function(e, t, n) {
		return t.namespaceURI === U ? e === "svg" : t.namespaceURI === Wt ? e === "svg" && (n === "annotation-xml" || Zt[n]) : !!cn[e];
	}, dn = function(e, t, n) {
		return t.namespaceURI === U ? e === "math" : t.namespaceURI === Gt ? e === "math" && $t[n] : !!ln[e];
	}, fn = function(e, t, n) {
		return t.namespaceURI === Gt && !$t[n] || t.namespaceURI === Wt && !Zt[n] ? !1 : !ln[e] && (en[e] || !cn[e]);
	}, G = function(e) {
		let t = g(e);
		(!t || !t.tagName) && (t = {
			namespaceURI: Kt,
			tagName: "template"
		});
		let n = se(e.tagName), r = se(t.tagName);
		return Jt[e.namespaceURI] ? e.namespaceURI === Gt ? un(n, t, r) : e.namespaceURI === Wt ? dn(n, t, r) : e.namespaceURI === U ? fn(n, t, r) : !!(tn === "application/xhtml+xml" && Jt[e.namespaceURI]) : !1;
	}, K = function(e) {
		ie(t.removed, { element: e });
		try {
			g(e).removeChild(e);
		} catch (t) {
			if (pe(e), !g(e)) throw _e("a node selected for removal could not be detached from its tree and cannot be safely returned; refusing to sanitize in place");
		}
	}, pn = function(e, t, n) {
		try {
			e.removeAttributeNode(t);
		} catch (t) {
			try {
				e.removeAttribute(n);
			} catch (e) {}
		}
	}, q = function(e) {
		hn(e);
		let t = he(e);
		if (t) {
			let e = [];
			te(t, (t) => {
				ie(e, t);
			}), te(e, (e) => {
				try {
					pe(e);
				} catch (e) {}
			});
		}
		let n = y(e);
		if (n) for (let t = n.length - 1; t >= 0; --t) {
			let r = n[t], i = r && r.name;
			typeof i == "string" && pn(e, r, i);
		}
	}, J = function(e, n, r) {
		if (!r) try {
			r = n.getAttributeNode(e);
		} catch (e) {
			r = null;
		}
		ie(t.removed, {
			attribute: r || null,
			from: n
		});
		try {
			r ? n.removeAttributeNode(r) : n.removeAttribute(e);
		} catch (t) {
			try {
				n.removeAttribute(e);
			} catch (e) {}
		}
		if (e === "is") {
			if (B || V) try {
				K(n);
			} catch (e) {}
			else try {
				n.setAttribute(e, "");
			} catch (e) {}
		}
	}, mn = function(e) {
		let t = y(e);
		if (t) for (let n = t.length - 1; n >= 0; --n) {
			let r = t[n], i = r && r.name;
			typeof i != "string" || F[W(i)] || pn(e, r, i);
		}
	}, hn = function(e) {
		let t = [e];
		for (; t.length > 0;) {
			let e = t.pop();
			et(e) === w.element && mn(e);
			let n = he(e);
			if (n) for (let e = n.length - 1; e >= 0; --e) t.push(n[e]);
		}
	}, gn = function(e, t) {
		return Et ? e === "patchsrc" || e === "for" && t !== "label" && t !== "output" : !1;
	}, _n = function(e) {
		if (!Et) return;
		let t = [e];
		for (; t.length > 0;) {
			let e = t.pop(), n = et(e);
			if (n === w.processingInstruction || n === w.comment && v(Ue, e.data)) {
				try {
					pe(e);
				} catch (e) {}
				continue;
			}
			if (n === w.element) {
				let t = e, n = W(tt(e));
				try {
					t.hasAttribute && t.hasAttribute("patchsrc") && t.removeAttribute("patchsrc"), t.hasAttribute && t.hasAttribute("for") && gn("for", n) && t.removeAttribute("for");
				} catch (e) {}
			}
			let r = he(e);
			if (r) for (let e = r.length - 1; e >= 0; --e) t.push(r[e]);
		}
	}, vn = function(e) {
		let t = null, r = null;
		if (jt) e = "<remove></remove>" + e;
		else {
			let t = le(e, /^[\r\n\t ]+/);
			r = t && t[0];
		}
		tn === "application/xhtml+xml" && Kt === U && (e = "<html xmlns=\"http://www.w3.org/1999/xhtml\"><head></head><body>" + e + "</body></html>");
		let i = E ? k(e) : e;
		if (Kt === U) try {
			t = new u().parseFromString(i, tn);
		} catch (e) {}
		if (!t || !t.documentElement) {
			t = st.createDocument(Kt, "template", null);
			try {
				t.documentElement.innerHTML = qt ? nt : i;
			} catch (e) {}
		}
		let a = t.body || t.documentElement;
		return e && r && a.insertBefore(n.createTextNode(r), a.childNodes[0] || null), Kt === U ? M.call(t, Dt ? "html" : "body")[0] : Dt ? t.documentElement : a;
	}, Y = function(e) {
		let t = Ke ? Ke(e) : e.ownerDocument;
		return j.call(t || e, e, l.SHOW_ELEMENT | l.SHOW_COMMENT | l.SHOW_TEXT | l.SHOW_PROCESSING_INSTRUCTION | l.SHOW_CDATA_SECTION, null);
	}, yn = function(e) {
		return e = ue(e, ut, " "), e = ue(e, dt, " "), e = ue(e, ft, " "), e;
	}, bn = function(e) {
		var t;
		e.normalize();
		let n = Ke ? Ke(e) : e.ownerDocument, r = j.call(n || e, e, l.SHOW_TEXT | l.SHOW_COMMENT | l.SHOW_CDATA_SECTION | l.SHOW_PROCESSING_INSTRUCTION, null), i = r.nextNode();
		for (; i;) i.data = yn(i.data), i = r.nextNode();
		let a = (t = e.querySelectorAll) == null ? void 0 : t.call(e, "template");
		a && te(a, (e) => {
			Z(e.content) && bn(e.content);
		});
	}, X = function(e) {
		let t = ve ? ve(e) : null;
		return typeof t != "string" || W(t) !== "form" ? !1 : typeof e.nodeName != "string" || typeof e.textContent != "string" || typeof e.removeChild != "function" || e.attributes !== y(e) || typeof e.removeAttribute != "function" || typeof e.setAttribute != "function" || typeof e.namespaceURI != "string" || typeof e.insertBefore != "function" || typeof e.hasChildNodes != "function" || e.nodeType !== b(e) || e.childNodes !== he(e);
	}, Z = function(e) {
		if (!b || typeof e != "object" || !e) return !1;
		try {
			return b(e) === w.documentFragment;
		} catch (e) {
			return !1;
		}
	}, Q = function(e) {
		if (!b || typeof e != "object" || !e) return !1;
		try {
			return typeof b(e) == "number";
		} catch (e) {
			return !1;
		}
	};
	function $(e, n, r) {
		e.length !== 0 && te(e, (e) => {
			e.call(t, n, r, rn);
		});
	}
	let xn = function(e, t) {
		return !!(Et && e.hasChildNodes() && !Q(e.firstElementChild) && v(He, e.textContent) && v(He, e.innerHTML) || Et && e.namespaceURI === U && qe[t] && (Q(e.firstElementChild) || typeof e.textContent == "string" && v(Je[t], e.textContent)) || e.nodeType === w.processingInstruction || Et && e.nodeType === w.comment && v(Ue, e.data));
	}, Sn = function(e, t) {
		return e instanceof RegExp ? v(e, t) : e instanceof Function && !!e(t, ...[...arguments].slice(2));
	}, Cn = function(e, t, n) {
		if (!L[t] && kn(t) && Sn(I.tagNameCheck, t)) return !1;
		if (Ft && !Rt[t]) {
			let t = g(e), r = he(e);
			if (r && t) {
				let i = r.length;
				for (let a = i - 1; a >= 0; --a) {
					let i = e === n ? ee(r[a], !0) : r[a];
					t.insertBefore(i, me(e));
				}
			}
		}
		return K(e), !0;
	}, wn = function(e, t, n, r) {
		return e.length === 0 ? t : t === n || t === r ? S(t) : t;
	}, Tn = function(e, t) {
		return e === t || g(e) !== null ? !1 : (It && hn(e), !0);
	}, En = function(e, n) {
		if ($(N.beforeSanitizeElements, e, null), Tn(e, n)) return !0;
		if (X(e)) return K(e), !0;
		let r = W(tt(e));
		if (P = wn(N.uponSanitizeElement, P, yt, kt), $(N.uponSanitizeElement, e, {
			tagName: r,
			allowedTags: P
		}), Tn(e, n)) return !0;
		if (xn(e, r)) return K(e), !0;
		if (L[r] || !(R.tagCheck instanceof Function && R.tagCheck(r)) && !P[r]) {
			let t = Cn(e, r, n);
			return t === !1 && $(N.afterSanitizeElements, e, null), t;
		}
		if (et(e) === w.element && !G(e) || (r === "noscript" || r === "noembed" || r === "noframes") && v(We, e.innerHTML)) return K(e), !0;
		if (z && e.nodeType === w.text) {
			let n = yn(e.textContent);
			e.textContent !== n && (ie(t.removed, { element: e.cloneNode() }), e.textContent = n);
		}
		return $(N.afterSanitizeElements, e, null), !1;
	}, Dn = function(e, t, r) {
		if (xt[t] || gn(t, e) || Mt && (t === "id" || t === "name") && (r in n || r in an)) return !1;
		let i = F[t] || R.attributeCheck instanceof Function && R.attributeCheck(t, e);
		return Ct && v(pt, t) || St && v(mt, t) ? !0 : i ? Ht[t] || v(vt, ue(r, gt, "")) || (t === "src" || t === "xlink:href" || t === "href") && e !== "script" && de(r, "data:") === 0 && Bt[e] || wt && !v(ht, ue(r, gt, "")) ? !0 : !r : kn(e) && Sn(I.tagNameCheck, e) && Sn(I.attributeNameCheck, t, e) || t === "is" && I.allowCustomizedBuiltInElements && Sn(I.tagNameCheck, r);
	}, On = x({}, [
		"annotation-xml",
		"color-profile",
		"font-face",
		"font-face-format",
		"font-face-name",
		"font-face-src",
		"font-face-uri",
		"missing-glyph"
	]), kn = function(e) {
		return !On[se(e)] && v(_t, e);
	}, An = function(e, t, n, r) {
		if (E && typeof m == "object" && typeof m.getAttributeType == "function" && !n) switch (m.getAttributeType(e, t)) {
			case "TrustedHTML": return k(r);
			case "TrustedScriptURL": return at(r);
		}
		return r;
	}, jn = function(e, n, r, i) {
		try {
			r ? e.setAttributeNS(r, n, i) : e.setAttribute(n, i), X(e) ? K(e) : re(t.removed);
		} catch (t) {
			J(n, e);
		}
	}, Mn = function(e) {
		$(N.beforeSanitizeAttributes, e, null);
		let t = e.attributes;
		if (!t || X(e)) return;
		F = wn(N.uponSanitizeAttribute, F, bt, At);
		let n = {
			attrName: "",
			attrValue: "",
			keepAttr: !0,
			allowedAttributes: F,
			forceKeepAttr: void 0
		}, r = t.length, i = W(e.nodeName);
		for (; r--;) {
			let a = t[r], o = a.name, s = a.namespaceURI, c = a.value, l = W(o), u = c, d = o === "value" ? u : fe(u);
			if (n.attrName = l, n.attrValue = d, n.keepAttr = !0, n.forceKeepAttr = void 0, $(N.uponSanitizeAttribute, e, n), d = n.attrValue, Nt && (l === "id" || l === "name") && de(d, Pt) !== 0 && (J(o, e, a), d = Pt + d), Et && v(/((--!?|])>)|<\/(style|script|title|xmp|textarea|noscript|iframe|noembed|noframes)/i, d)) {
				J(o, e, a);
				continue;
			}
			if (l === "attributename" && le(d, "href")) {
				J(o, e, a);
				continue;
			}
			if (!n.forceKeepAttr) {
				if (!n.keepAttr) {
					J(o, e, a);
					continue;
				}
				if (!Tt && v(Ge, d)) {
					J(o, e, a);
					continue;
				}
				if (z && (d = yn(d)), !Dn(i, l, d)) {
					J(o, e, a);
					continue;
				}
				d = An(i, l, s, d), d !== u && jn(e, o, s, d);
			}
		}
		$(N.afterSanitizeAttributes, e, null);
	}, Nn = function(e) {
		let t = null, n = Y(e);
		for ($(N.beforeSanitizeShadowDOM, e, null); t = n.nextNode();) if ($(N.uponSanitizeShadowNode, t, null), En(t, e), Mn(t), Z(t.content) && Nn(t.content), et(t) === w.element) {
			let e = ge(t);
			Z(e) && (Pn(e), Nn(e));
		}
		$(N.afterSanitizeShadowDOM, e, null);
	}, Pn = function(e) {
		let t = [{
			node: e,
			shadow: null
		}];
		for (; t.length > 0;) {
			let e = t.pop();
			if (e.shadow) {
				Nn(e.shadow);
				continue;
			}
			let n = e.node, r = et(n) === w.element, i = he(n);
			if (i) for (let e = i.length - 1; e >= 0; --e) t.push({
				node: i[e],
				shadow: null
			});
			if (r) {
				let e = ve ? ve(n) : null;
				if (typeof e == "string" && W(e) === "template") {
					let e = n.content;
					Z(e) && t.push({
						node: e,
						shadow: null
					});
				}
			}
			if (r) {
				let e = ge(n);
				Z(e) && t.push({
					node: null,
					shadow: e
				}, {
					node: e,
					shadow: null
				});
			}
		}
	};
	return t.sanitize = function(e) {
		let n = arguments.length > 1 && arguments[1] !== void 0 ? arguments[1] : {}, i = null, a = null, o = null, s = null;
		if (qt = !e, qt && (e = "<!-->"), typeof e != "string" && !Q(e) && (e = ye(e), typeof e != "string")) throw _e("dirty is not a string, aborting");
		if (!t.isSupported) return e;
		Ot ? (P = kt, F = At) : sn(n), (N.uponSanitizeElement.length > 0 || N.uponSanitizeAttribute.length > 0) && (P = S(P)), N.uponSanitizeAttribute.length > 0 && (F = S(F)), t.removed = [];
		let c = It && typeof e != "string" && Q(e);
		if (c) {
			_n(e);
			let t = tt(e);
			if (typeof t == "string") {
				let n = W(t);
				if (!P[n] || L[n]) throw q(e), _e("root node is forbidden and cannot be sanitized in-place");
			}
			if (X(e)) throw q(e), _e("root node is clobbered and cannot be sanitized in-place");
			try {
				Pn(e);
			} catch (t) {
				throw q(e), t;
			}
		} else if (Q(e)) i = vn("<!---->"), a = i.ownerDocument.importNode(e, !0), a.nodeType === w.element && a.nodeName === "BODY" || a.nodeName === "HTML" ? i = a : i.appendChild(a), Pn(a);
		else {
			if (!B && !z && !Dt && e.indexOf("<") === -1) return E && H ? k(e) : e;
			if (i = vn(e), !i) return B ? null : H ? nt : "";
		}
		i && jt && K(i.firstChild);
		let l = c ? e : i;
		try {
			let e = Y(l);
			for (; o = e.nextNode();) En(o, l), Mn(o), Z(o.content) && Nn(o.content);
		} catch (n) {
			throw c && (q(e), te(t.removed, (e) => {
				e.element && hn(e.element);
			})), n;
		}
		if (c) return te(t.removed, (e) => {
			e.element && hn(e.element);
		}), z && bn(e), e;
		if (B) {
			if (z && bn(i), V) for (s = ct.call(i.ownerDocument); i.firstChild;) s.appendChild(i.firstChild);
			else s = i;
			return (F.shadowroot || F.shadowrootmode) && (s = lt.call(r, s, !0)), s;
		}
		let u = Dt ? i.outerHTML : i.innerHTML;
		return Dt && P["!doctype"] && i.ownerDocument && i.ownerDocument.doctype && i.ownerDocument.doctype.name && v(Be, i.ownerDocument.doctype.name) && (u = "<!DOCTYPE " + i.ownerDocument.doctype.name + ">\n" + u), z && (u = yn(u)), E && H ? k(u) : u;
	}, t.setConfig = function() {
		let e = arguments.length > 0 && arguments[0] !== void 0 ? arguments[0] : {};
		sn(e), Ot = !0, kt = P, At = F;
	}, t.clearConfig = function() {
		rn = null, Ot = !1, kt = null, At = null, E = D, nt = "";
	}, t.isValidAttribute = function(e, t, n) {
		rn || sn({});
		let r = W(e), i = W(t);
		return Dn(r, i, n);
	}, t.addHook = function(e, t) {
		typeof t == "function" && _(N, e) && ie(N[e], t);
	}, t.removeHook = function(e, t) {
		if (_(N, e)) {
			if (t !== void 0) {
				let n = ne(N[e], t);
				return n === -1 ? void 0 : ae(N[e], n, 1)[0];
			}
			return re(N[e]);
		}
	}, t.removeHooks = function(e) {
		_(N, e) && (N[e] = []);
	}, t.removeAllHooks = function() {
		N = Ze();
	}, t;
}
var et = $e();
//#endregion
//#region \0@oxc-project+runtime@0.147.0/helpers/esm/typeof.js
function tt(e) {
	"@babel/helpers - typeof";
	return tt = typeof Symbol == "function" && typeof Symbol.iterator == "symbol" ? function(e) {
		return typeof e;
	} : function(e) {
		return e && typeof Symbol == "function" && e.constructor === Symbol && e !== Symbol.prototype ? "symbol" : typeof e;
	}, tt(e);
}
//#endregion
//#region \0@oxc-project+runtime@0.147.0/helpers/esm/toPrimitive.js
function E(e, t) {
	if (tt(e) != "object" || !e) return e;
	var n = e[Symbol.toPrimitive];
	if (n !== void 0) {
		var r = n.call(e, t || "default");
		if (tt(r) != "object") return r;
		throw TypeError("@@toPrimitive must return a primitive value.");
	}
	return (t === "string" ? String : Number)(e);
}
//#endregion
//#region \0@oxc-project+runtime@0.147.0/helpers/esm/toPropertyKey.js
function nt(e) {
	var t = E(e, "string");
	return tt(t) == "symbol" ? t : t + "";
}
//#endregion
//#region \0@oxc-project+runtime@0.147.0/helpers/esm/defineProperty.js
function D(e, t, n) {
	return (t = nt(t)) in e ? Object.defineProperty(e, t, {
		value: n,
		enumerable: !0,
		configurable: !0,
		writable: !0
	}) : e[t] = n, e;
}
//#endregion
//#region \0@oxc-project+runtime@0.147.0/helpers/esm/objectSpread2.js
function rt(e, t) {
	var n = Object.keys(e);
	if (Object.getOwnPropertySymbols) {
		var r = Object.getOwnPropertySymbols(e);
		t && (r = r.filter(function(t) {
			return Object.getOwnPropertyDescriptor(e, t).enumerable;
		})), n.push.apply(n, r);
	}
	return n;
}
function O(e) {
	for (var t = 1; t < arguments.length; t++) {
		var n = arguments[t] == null ? {} : arguments[t];
		t % 2 ? rt(Object(n), !0).forEach(function(t) {
			D(e, t, n[t]);
		}) : Object.getOwnPropertyDescriptors ? Object.defineProperties(e, Object.getOwnPropertyDescriptors(n)) : rt(Object(n)).forEach(function(t) {
			Object.defineProperty(e, t, Object.getOwnPropertyDescriptor(n, t));
		});
	}
	return e;
}
//#endregion
//#region \0@oxc-project+runtime@0.147.0/helpers/esm/asyncToGenerator.js
function it(e, t, n, r, i, a, o) {
	try {
		var s = e[a](o), c = s.value;
	} catch (e) {
		n(e);
		return;
	}
	s.done ? t(c) : Promise.resolve(c).then(r, i);
}
function k(e) {
	return function() {
		var t = this, n = arguments;
		return new Promise(function(r, i) {
			var a = e.apply(t, n);
			function o(e) {
				it(a, r, i, o, s, "next", e);
			}
			function s(e) {
				it(a, r, i, o, s, "throw", e);
			}
			o(void 0);
		});
	};
}
//#endregion
//#region node_modules/marked/lib/marked.esm.js
var at;
function ot() {
	return {
		async: !1,
		breaks: !1,
		extensions: null,
		gfm: !0,
		hooks: null,
		pedantic: !1,
		renderer: null,
		silent: !1,
		tokenizer: null,
		walkTokens: null
	};
}
var A = ot();
function st(e) {
	A = e;
}
var j = { exec: () => null };
function ct(e) {
	let t = [];
	return (n) => {
		let r = Math.max(0, Math.min(3, n - 1)), i = t[r];
		return i || (i = e(r), t[r] = i), i;
	};
}
function M(e, t = "") {
	let n = typeof e == "string" ? e : e.source, r = {
		replace: (e, t) => {
			let i = typeof t == "string" ? t : t.source;
			return i = i.replace(N.caret, "$1"), n = n.replace(e, i), r;
		},
		getRegex: () => new RegExp(n, t)
	};
	return r;
}
var lt = ((e = "") => {
	try {
		return !!RegExp("(?<=1)(?<!1)" + e);
	} catch (e) {
		return !1;
	}
})(), N = {
	codeRemoveIndent: /^(?: {1,4}| {0,3}\t)/gm,
	outputLinkReplace: /\\([\[\]])/g,
	indentCodeCompensation: /^(\s+)(?:```)/,
	beginningSpace: /^\s+/,
	endingHash: /#$/,
	startingSpaceChar: /^ /,
	endingSpaceChar: / $/,
	nonSpaceChar: /[^ ]/,
	newLineCharGlobal: /\n/g,
	tabCharGlobal: /\t/g,
	multipleSpaceGlobal: /\s+/g,
	blankLine: /^[ \t]*$/,
	doubleBlankLine: /\n[ \t]*\n[ \t]*$/,
	blockquoteStart: /^ {0,3}>/,
	blockquoteSetextReplace: /\n {0,3}((?:=+|-+) *)(?=\n|$)/g,
	blockquoteSetextReplace2: /^ {0,3}>[ \t]?/gm,
	listReplaceNesting: /^ {1,4}(?=( {4})*[^ ])/g,
	listIsTask: /^\[[ xX]\] +\S/,
	listReplaceTask: /^\[[ xX]\] +/,
	listTaskCheckbox: /\[[ xX]\]/,
	anyLine: /\n.*\n/,
	hrefBrackets: /^<(.*)>$/,
	tableDelimiter: /[:|]/,
	tableAlignChars: /^\||\| *$/g,
	tableRowBlankLine: /\n[ \t]*$/,
	tableAlignRight: /^ *-+: *$/,
	tableAlignCenter: /^ *:-+: *$/,
	tableAlignLeft: /^ *:-+ *$/,
	startATag: /^<a /i,
	endATag: /^<\/a>/i,
	startPreScriptTag: /^<(pre|code|kbd|script)(\s|>)/i,
	endPreScriptTag: /^<\/(pre|code|kbd|script)(\s|>)/i,
	startAngleBracket: /^</,
	endAngleBracket: />$/,
	pedanticHrefTitle: /^([^'"]*[^\s])\s+(['"])(.*)\2/,
	unicodeAlphaNumeric: RegExp("[\\p{L}\\p{N}]", "u"),
	escapeTest: /[&<>"']/,
	escapeReplace: /[&<>"']/g,
	escapeTestNoEncode: /[<>"']|&(?!(#\d{1,7}|#[Xx][a-fA-F0-9]{1,6}|\w+);)/,
	escapeReplaceNoEncode: /[<>"']|&(?!(#\d{1,7}|#[Xx][a-fA-F0-9]{1,6}|\w+);)/g,
	caret: /(^|[^\[])\^/g,
	percentDecode: /%25/g,
	findPipe: /\|/g,
	splitPipe: / \|/,
	slashPipe: /\\\|/g,
	carriageReturn: /\r\n|\r/g,
	spaceLine: /^ +$/gm,
	notSpaceStart: /^\S*/,
	endingNewline: /\n$/,
	listItemRegex: (e) => RegExp(`^( {0,3}${e})((?:[	 ][^\\n]*)?(?:\\n|$))`),
	nextBulletRegex: ct((e) => RegExp(`^ {0,${e}}(?:[*+-]|\\d{1,9}[.)])((?:[ 	][^\\n]*)?(?:\\n|$))`)),
	hrRegex: ct((e) => RegExp(`^ {0,${e}}((?:- *){3,}|(?:_ *){3,}|(?:\\* *){3,})(?:\\n+|$)`)),
	fencesBeginRegex: ct((e) => RegExp(`^ {0,${e}}(?:\`\`\`|~~~)`)),
	headingBeginRegex: ct((e) => RegExp(`^ {0,${e}}#`)),
	htmlBeginRegex: ct((e) => RegExp(`^ {0,${e}}<(?:[a-z].*>|!--)`, "i")),
	blockquoteBeginRegex: ct((e) => RegExp(`^ {0,${e}}>`))
}, ut = /^(?:[ \t]*(?:\n|$))+/, dt = /^((?: {4}| {0,3}\t)[^\n]+(?:\n(?:[ \t]*(?:\n|$))*)?)+/, ft = /^ {0,3}(`{3,}(?=[^`\n]*(?:\n|$))|~{3,})([^\n]*)(?:\n|$)(?:|([\s\S]*?)(?:\n|$))(?: {0,3}\1[~`]* *(?=\n|$)|$)/, pt = /^ {0,3}((?:-[\t ]*){3,}|(?:_[ \t]*){3,}|(?:\*[ \t]*){3,})(?:\n+|$)/, mt = /^ {0,3}(#{1,6})(?=\s|$)(.*)(?:\n+|$)/, ht = / {0,3}(?:[*+-]|\d{1,9}[.)])/, gt = /^(?!bull |blockCode|fences|blockquote|heading|html|table)((?:.|\n(?!\s*?\n|bull |blockCode|fences|blockquote|heading|html|table))+?)\n {0,3}(=+|-+) *(?:\n+|$)/, _t = M(gt).replace(/bull/g, ht).replace(/blockCode/g, /(?: {4}| {0,3}\t)/).replace(/fences/g, / {0,3}(?:`{3,}|~{3,})/).replace(/blockquote/g, / {0,3}>/).replace(/heading/g, / {0,3}#{1,6}(?:\s|$)/).replace(/html/g, / {0,3}<[^\n>]+>\n/).replace(/\|table/g, "").getRegex(), vt = M(gt).replace(/bull/g, ht).replace(/blockCode/g, /(?: {4}| {0,3}\t)/).replace(/fences/g, / {0,3}(?:`{3,}|~{3,})/).replace(/blockquote/g, / {0,3}>/).replace(/heading/g, / {0,3}#{1,6}(?:\s|$)/).replace(/html/g, / {0,3}<[^\n>]+>\n/).replace(/table/g, / {0,3}\|?(?:[:\- ]*\|)+[\:\- ]*\n/).getRegex(), P = /^([^\n]+(?:\n(?!hr|heading|lheading|blockquote|fences|list|html|table|[ \t]+\n)[^\n]+)*)/, yt = /^[^\n]+/, F = /(?!\s*\])(?:\\[\s\S]|[^\[\]\\])+/, bt = M(/^ {0,3}\[(label)\]: *(?:\n[ \t]*)?([^<\s][^\s]*|<.*?>)(?:(?: +(?:\n[ \t]*)?| *\n[ \t]*)(title))? *(?:\n+|$)/).replace("label", F).replace("title", /(?:"(?:\\"?|[^"\\])*"|'[^'\n]*(?:\n[^'\n]+)*\n?'|\([^()]*\))/).getRegex(), I = M(/^(bull)([ \t][^\n]*?)?(?:\n|$)/).replace(/bull/g, ht).getRegex(), L = "address|article|aside|base|basefont|blockquote|body|caption|center|col|colgroup|dd|details|dialog|dir|div|dl|dt|fieldset|figcaption|figure|footer|form|frame|frameset|h[1-6]|head|header|hr|html|iframe|legend|li|link|main|menu|menuitem|meta|nav|noframes|ol|optgroup|option|p|param|search|section|summary|table|tbody|td|tfoot|th|thead|title|tr|track|ul", xt = /<!--(?:-?>|[\s\S]*?(?:-->|$))/, R = M("^ {0,3}(?:<(script|pre|style|textarea)[\\s>][\\s\\S]*?(?:</\\1>[^\\n]*\\n*|$)|comment[^\\n]*(\\n+|$)|<\\?[\\s\\S]*?(?:\\?>[^\\n]*\\n*|$)|<![A-Z][\\s\\S]*?(?:>[^\\n]*\\n*|$)|<!\\[CDATA\\[[\\s\\S]*?(?:\\]\\]>[^\\n]*\\n*|$)|</?(tag)(?: +|\\n|/?>)[\\s\\S]*?(?:(?:\\n[ 	]*)+\\n|$)|<(?!script|pre|style|textarea)([a-z][\\w-]*)(?:attribute)*? */?>(?=[ \\t]*(?:\\n|$))[\\s\\S]*?(?:(?:\\n[ 	]*)+\\n|$)|</(?!script|pre|style|textarea)[a-z][\\w-]*\\s*>(?=[ \\t]*(?:\\n|$))[\\s\\S]*?(?:(?:\\n[ 	]*)+\\n|$))", "i").replace("comment", xt).replace("tag", L).replace("attribute", / +[a-zA-Z:_][\w.:-]*(?: *= *"[^"\n]*"| *= *'[^'\n]*'| *= *[^\s"'=<>`]+)?/).getRegex(), St = (e) => M(P).replace("hr", pt).replace("heading", " {0,3}#{1,6}(?:\\s|$)").replace("|lheading", "").replace("|table", "").replace("blockquote", " {0,3}>").replace("fences", " {0,3}(?:`{3,}(?=[^`\\n]*(?:\\n|$))|~~~)[^\\n]*(?:\\n|$)").replace("list", e).replace("html", "</?(?:tag)(?: +|\\n|/?>)|<(?:script|pre|style|textarea|!--)").replace("tag", L).getRegex(), Ct = St(/ {0,3}(?:[*+-]|1[.)])[ \t]+[^ \t\n]/), wt = St(/ {0,3}(?:[*+-]|\d{1,9}[.)])(?:[ \t]|\n|$)/), Tt = {
	blockquote: M(/^( {0,3}> ?(paragraph|[^\n]*)(?:\n|$))+/).replace("paragraph", wt).getRegex(),
	code: dt,
	def: bt,
	fences: ft,
	heading: mt,
	hr: pt,
	html: R,
	lheading: _t,
	list: I,
	newline: ut,
	paragraph: Ct,
	table: j,
	text: yt
}, z = M("^ *([^\\n ].*)\\n {0,3}((?:\\| *)?:?-+:? *(?:\\| *:?-+:? *)*(?:\\| *)?)(?:\\n((?:(?! *\\n|hr|heading|blockquote|code|fences|list|html).*(?:\\n|$))*)\\n*|$)").replace("hr", pt).replace("heading", " {0,3}#{1,6}(?:\\s|$)").replace("blockquote", " {0,3}>").replace("code", "(?: {4}| {0,3}	)[^\\n]").replace("fences", " {0,3}(?:`{3,}(?=[^`\\n]*(?:\\n|$))|~~~)[^\\n]*(?:\\n|$)").replace("list", " {0,3}(?:[*+-]|1[.)])[ \\t]").replace("html", "</?(?:tag)(?: +|\\n|/?>)|<(?:script|pre|style|textarea|!--)").replace("tag", L).getRegex(), Et = O(O({}, Tt), {}, {
	lheading: vt,
	table: z,
	paragraph: M(P).replace("hr", pt).replace("heading", " {0,3}#{1,6}(?:\\s|$)").replace("|lheading", "").replace("table", z).replace("blockquote", " {0,3}>").replace("fences", " {0,3}(?:`{3,}(?=[^`\\n]*(?:\\n|$))|~~~)[^\\n]*(?:\\n|$)").replace("list", " {0,3}(?:[*+-]|1[.)])[ \\t]+[^ \\t\\n]").replace("html", "</?(?:tag)(?: +|\\n|/?>)|<(?:script|pre|style|textarea|!--)").replace("tag", L).getRegex()
}), Dt = O(O({}, Tt), {}, {
	html: M("^ *(?:comment *(?:\\n|\\s*$)|<(tag)[\\s\\S]+?</\\1> *(?:\\n{2,}|\\s*$)|<tag(?:\"[^\"]*\"|'[^']*'|\\s[^'\"/>\\s]*)*?/?> *(?:\\n{2,}|\\s*$))").replace("comment", xt).replace(/tag/g, "(?!(?:a|em|strong|small|s|cite|q|dfn|abbr|data|time|code|var|samp|kbd|sub|sup|i|b|u|mark|ruby|rt|rp|bdi|bdo|span|br|wbr|ins|del|img)\\b)\\w+(?!:|[^\\w\\s@]*@)\\b").getRegex(),
	def: /^ *\[([^\]]+)\]: *<?([^\s>]+)>?(?: +(["(][^\n]+[")]))? *(?:\n+|$)/,
	heading: /^(#{1,6})(.*)(?:\n+|$)/,
	fences: j,
	lheading: /^(.+?)\n {0,3}(=+|-+) *(?:\n+|$)/,
	paragraph: M(P).replace("hr", pt).replace("heading", " *#{1,6} *[^\n]").replace("lheading", _t).replace("|table", "").replace("blockquote", " {0,3}>").replace("|fences", "").replace("|list", "").replace("|html", "").replace("|tag", "").getRegex()
}), Ot = /^\\([!"#$%&'()*+,\-./:;<=>?@\[\]\\^_`{|}~])/, kt = /^(`+)([^`]|[^`][\s\S]*?[^`])\1(?!`)/, At = /^( {2,}|\\)\n(?!\s*$)/, jt = /^(`+|[^`])(?:(?= {2,}\n)|[\s\S]*?(?:(?=[\\<!\[`*_]|\b_|$)|[^ ](?= {2,}\n)))/, B = RegExp("[\\p{P}\\p{S}]", "u"), V = RegExp("[\\s\\p{P}\\p{S}]", "u"), H = RegExp("[^\\s\\p{P}\\p{S}]", "u"), Mt = M(/^((?![*_])punctSpace)/, "u").replace(/punctSpace/g, V).getRegex(), Nt = RegExp("[\\p{Pi}\\p{Ps}\"']", "u"), Pt = RegExp("(?!~)[\\p{P}\\p{S}]", "u"), Ft = RegExp("(?!~)[\\s\\p{P}\\p{S}]", "u"), It = RegExp("(?:[^\\s\\p{P}\\p{S}]|~)", "u"), Lt = M(/link|precode-code|html/, "g").replace("link", RegExp("\\[(?:[^\\[\\]`]|(?<a>`+)[^`]+\\k<a>(?!`))*?\\]\\((?:\\\\[\\s\\S]|[^\\\\\\(\\)]|\\((?:\\\\[\\s\\S]|[^\\\\\\(\\)])*\\))*\\)", "")).replace("precode-", lt ? "(?<!`)()" : "(^^|[^`])").replace("code", RegExp("(?<b>`+)[^`]+\\k<b>(?!`)", "")).replace("html", /<(?! )[^<>]*?>/).getRegex(), Rt = /^(?:\*+(?:((?!\*)punct)|([^\s*]))?)|^_+(?:((?!_)punct)|([^\s_]))?/, zt = M(Rt, "u").replace(/punct/g, B).getRegex(), Bt = M(Rt, "u").replace(/punct/g, Pt).getRegex(), Vt = M(/^(?:\*+(?:((?!\*)(?!openQuote)punct)|([^\s*]))?)|^_+(?:((?!_)(?!openQuote)punct)|([^\s_]))?/, "u").replace(/openQuote/g, Nt).replace(/punct/g, B).getRegex(), Ht = "^[^_*]*?__[^_*]*?\\*[^_*]*?(?=__)|[^*]+(?=[^*])|(?!\\*)punct(\\*+)(?=[\\s]|$)|notPunctSpace(\\*+)(?!\\*)(?=punctSpace|$)|(?!\\*)punctSpace(\\*+)(?=notPunctSpace)|[\\s](\\*+)(?!\\*)(?=punct)|(?!\\*)punct(\\*+)(?!\\*)(?=punct)|notPunctSpace(\\*+)(?=notPunctSpace)", Ut = M(Ht, "gu").replace(/notPunctSpace/g, H).replace(/punctSpace/g, V).replace(/punct/g, B).getRegex(), Wt = M(Ht, "gu").replace(/notPunctSpace/g, It).replace(/punctSpace/g, Ft).replace(/punct/g, Pt).getRegex(), Gt = M("^[^_*]*?__[^_*]*?\\*[^_*]*?(?=__)|[^*]+(?=[^*])|(?!\\*)punct(\\*+)(?=[\\s]|$)|notPunctSpace(\\*+)(?!\\*)(?=punctSpace|$)|(?!\\*)[\\s](\\*+)(?=notPunctSpace)|[\\s](\\*+)(?!\\*)(?=punct)|(?!\\*)punct(\\*+)(?!\\*)(?=punct)|(?:(?!\\*)punct|notPunctSpace)(\\*+)(?!\\*)(?=notPunctSpace)", "gu").replace(/notPunctSpace/g, H).replace(/punctSpace/g, V).replace(/punct/g, B).getRegex(), U = M("^[^_*]*?\\*\\*[^_*]*?_[^_*]*?(?=\\*\\*)|[^_]+(?=[^_])|(?!_)punct(_+)(?=[\\s]|$)|notPunctSpace(_+)(?!_)(?=punctSpace|$)|(?!_)punctSpace(_+)(?=notPunctSpace)|[\\s](_+)(?!_)(?=punct)|(?!_)punct(_+)(?!_)(?=punct)", "gu").replace(/notPunctSpace/g, H).replace(/punctSpace/g, V).replace(/punct/g, B).getRegex(), Kt = M("^[^_*]*?\\*\\*[^_*]*?_[^_*]*?(?=\\*\\*)|[^_]+(?=[^_])|(?!_)punct(_+)(?=[\\s]|$)|notPunctSpace(_+)(?!_)(?=punctSpace|$)|(?!_)[\\s](_+)(?=notPunctSpace)|[\\s](_+)(?!_)(?=punct)|(?!_)punct(_+)(?!_)(?=punct)|(?:(?!_)punct|notPunctSpace)(_+)(?!_)(?=notPunctSpace)", "gu").replace(/notPunctSpace/g, H).replace(/punctSpace/g, V).replace(/punct/g, B).getRegex(), qt = M(/^~~?(?:((?!~)punct)|[^\s~])/, "u").replace(/punct/g, B).getRegex(), Jt = M("^[^~]+(?=[^~])|(?!~)punct(~~?)(?=[\\s]|$)|notPunctSpace(~~?)(?!~)(?=punctSpace|$)|(?!~)punctSpace(~~?)(?=notPunctSpace)|[\\s](~~?)(?!~)(?=punct)|(?!~)punct(~~?)(?!~)(?=punct)|notPunctSpace(~~?)(?=notPunctSpace)", "gu").replace(/notPunctSpace/g, H).replace(/punctSpace/g, V).replace(/punct/g, B).getRegex(), Yt = M(/\\(punct)/, "gu").replace(/punct/g, B).getRegex(), Xt = M(/^<(scheme:[^\s\x00-\x1f<>]*|email)>/).replace("scheme", /[a-zA-Z][a-zA-Z0-9+.-]{1,31}/).replace("email", /[a-zA-Z0-9.!#$%&'*+/=?^_`{|}~-]+(@)[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?(?:\.[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?)+(?![-_])/).getRegex(), Zt = M(xt).replace("(?:-->|$)", "-->").getRegex(), Qt = M("^comment|^</[a-zA-Z][\\w:-]*\\s*>|^<[a-zA-Z][\\w-]*(?:attribute)*?\\s*/?>|^<\\?[\\s\\S]*?\\?>|^<![a-zA-Z]+\\s[\\s\\S]*?>|^<!\\[CDATA\\[[\\s\\S]*?\\]\\]>").replace("comment", Zt).replace("attribute", /\s+[a-zA-Z:_][\w.:-]*(?:\s*=\s*"[^"]*"|\s*=\s*'[^']*'|\s*=\s*[^\s"'=<>`]+)?/).getRegex(), $t = /(?:\[(?:\\[\s\S]|[^\[\]\\])*\]|\\[\s\S]|`+(?!`)[^`]*?`+(?!`)|``+(?=\])|[^\[\]\\`])*?/, en = M(/^!?\[(label)\]\(\s*(href)(?:(?:[ \t]+(?:\n[ \t]*)?|\n[ \t]*)(title))?\s*\)/).replace("label", $t).replace("href", /<(?:\\.|[^\n<>\\])+>|[^ \t\n\x00-\x1f]+|(?=\))/).replace("title", /"(?:\\"?|[^"\\])*"|'(?:\\'?|[^'\\])*'|\((?:\\\)?|[^)\\])*\)/).getRegex(), tn = M(/^!?\[(label)\]\[(ref)\]/).replace("label", $t).replace("ref", F).getRegex(), nn = M(/^!?\[(ref)\](?:\[\])?/).replace("ref", F).getRegex(), W = M("reflink|nolink(?!\\()", "g").replace("reflink", tn).replace("nolink", nn).getRegex(), rn = /[hH][tT][tT][pP][sS]?|[fF][tT][pP]/, an = {
	_backpedal: j,
	anyPunctuation: Yt,
	autolink: Xt,
	blockSkip: Lt,
	br: At,
	code: kt,
	del: j,
	delLDelim: j,
	delRDelim: j,
	emStrongLDelim: zt,
	emStrongRDelimAst: Ut,
	emStrongRDelimUnd: U,
	escape: Ot,
	link: en,
	nolink: nn,
	punctuation: Mt,
	reflink: tn,
	reflinkSearch: W,
	tag: Qt,
	text: jt,
	url: j
}, on = O(O({}, an), {}, {
	emStrongLDelim: Vt,
	emStrongRDelimAst: Gt,
	emStrongRDelimUnd: Kt,
	link: M(/^!?\[(label)\]\((.*?)\)/).replace("label", $t).getRegex(),
	reflink: M(/^!?\[(label)\]\s*\[([^\]]*)\]/).replace("label", $t).getRegex()
}), sn = O(O({}, an), {}, {
	emStrongRDelimAst: Wt,
	emStrongLDelim: Bt,
	delLDelim: qt,
	delRDelim: Jt,
	url: M(/^((?:protocol):\/\/|www\.)(?:[a-zA-Z0-9\-]+\.?)+[^\s<]*|^email/).replace("protocol", rn).replace("email", /[A-Za-z0-9._+-]+(@)[a-zA-Z0-9-_]+(?:\.[a-zA-Z0-9-_]*[a-zA-Z0-9])+(?![-_])/).getRegex(),
	_backpedal: /(?:[^?!.,:;*_'"~()&]+|\([^)]*\)|&(?![a-zA-Z0-9]+;$)|[?!.,:;*_'"~)]+(?!$))+/,
	del: /^(~~?)(?=[^\s~])((?:\\[\s\S]|[^\\])*?(?:\\[\s\S]|[^\s~\\]))\1(?=[^~]|$)/,
	text: M(/^(`+|~+|[^`~])(?:(?=[`~])|(?= {2,}\n)|(?=[a-zA-Z0-9.!#$%&'*+\/=?_`{\|}~-]+@)|[\s\S]*?(?:(?=[\\<!\[`*~_]|\b_|protocol:\/\/|www\.|$)|[^ ](?= {2,}\n)|[^a-zA-Z0-9.!#$%&'*+\/=?_`{\|}~-](?=[a-zA-Z0-9.!#$%&'*+\/=?_`{\|}~-]+@)))/).replace("protocol", rn).getRegex()
}), cn = O(O({}, sn), {}, {
	br: M(At).replace("{2,}", "*").getRegex(),
	text: M(sn.text).replace("\\b_", "\\b_| {2,}\\n").replace(/\{2,\}/g, "*").getRegex()
}), ln = {
	normal: Tt,
	gfm: Et,
	pedantic: Dt
}, un = {
	normal: an,
	gfm: sn,
	breaks: cn,
	pedantic: on
}, dn = {
	"&": "&amp;",
	"<": "&lt;",
	">": "&gt;",
	"\"": "&quot;",
	"'": "&#39;"
}, fn = (e) => dn[e];
function G(e, t) {
	if (t) {
		if (N.escapeTest.test(e)) return e.replace(N.escapeReplace, fn);
	} else if (N.escapeTestNoEncode.test(e)) return e.replace(N.escapeReplaceNoEncode, fn);
	return e;
}
function K(e) {
	try {
		e = encodeURI(e).replace(N.percentDecode, "%");
	} catch (e) {
		return null;
	}
	return e;
}
function pn(e, t) {
	var n;
	let r = e.replace(N.findPipe, (e, t, n) => {
		let r = !1, i = t;
		for (; --i >= 0 && n[i] === "\\";) r = !r;
		return r ? "|" : " |";
	}).split(N.splitPipe), i = 0;
	if (r[0].trim() || r.shift(), r.length > 0 && !((n = r.at(-1)) != null && n.trim()) && r.pop(), t) {
		if (r.length > t) r.splice(t);
		else for (; r.length < t;) r.push("");
	}
	for (; i < r.length; i++) r[i] = r[i].trim().replace(N.slashPipe, "|");
	return r;
}
function q(e, t, n) {
	let r = e.length;
	if (r === 0) return "";
	let i = 0;
	for (; i < r;) {
		let a = e.charAt(r - i - 1);
		if (a === t && !n) i++;
		else if (a !== t && n) i++;
		else break;
	}
	return e.slice(0, r - i);
}
function J(e) {
	let t = e.split("\n"), n = t.length - 1;
	for (; n >= 0 && N.blankLine.test(t[n]);) n--;
	return t.length - n <= 2 ? e : t.slice(0, n + 1).join("\n");
}
function mn(e, t) {
	if (e.indexOf(t[1]) === -1) return -1;
	let n = 0;
	for (let r = 0; r < e.length; r++) if (e[r] === "\\") r++;
	else if (e[r] === t[0]) n++;
	else if (e[r] === t[1] && (n--, n < 0)) return r;
	return n > 0 ? -2 : -1;
}
function hn(e, t = 0) {
	let n = t, r = "";
	for (let t of e) if (t === "	") {
		let e = 4 - n % 4;
		r += " ".repeat(e), n += e;
	} else r += t, n++;
	return r;
}
function gn(e, t, n, r, i) {
	let a = t.href, o = t.title || null, s = e[1].replace(i.other.outputLinkReplace, "$1"), c = e[0].charAt(0) === "!";
	r.state.inLink = !0;
	let l = r.state.linkEmitted, u = r.state.inRawBlock;
	r.state.linkEmitted = !1;
	let d = r.inlineTokens(s), f = r.state.linkEmitted;
	if (r.state.linkEmitted = l, r.state.inLink = !1, !c) {
		if (f) {
			r.state.inRawBlock = u;
			return;
		}
		r.state.linkEmitted = !0;
	}
	return {
		type: c ? "image" : "link",
		raw: n,
		href: a,
		title: o,
		text: s,
		tokens: d
	};
}
function _n(e, t, n) {
	let r = e.match(n.other.indentCodeCompensation);
	if (r === null) return t;
	let i = r[1];
	return t.split("\n").map((e) => {
		let t = e.match(n.other.beginningSpace);
		if (t === null) return e;
		let [r] = t;
		return r.length >= i.length ? e.slice(i.length) : e;
	}).join("\n");
}
var vn = class {
	constructor(e) {
		D(this, "options", void 0), D(this, "rules", void 0), D(this, "lexer", void 0), this.options = e || A;
	}
	space(e) {
		let t = this.rules.block.newline.exec(e);
		if (t && t[0].length > 0) return {
			type: "space",
			raw: t[0]
		};
	}
	code(e) {
		let t = this.rules.block.code.exec(e);
		if (t) {
			let e = this.options.pedantic ? t[0] : J(t[0]);
			return {
				type: "code",
				raw: e,
				codeBlockStyle: "indented",
				text: e.replace(this.rules.other.codeRemoveIndent, "")
			};
		}
	}
	fences(e) {
		let t = this.rules.block.fences.exec(e);
		if (t) {
			let e = t[0], n = _n(e, t[3] || "", this.rules);
			return {
				type: "code",
				raw: e,
				lang: t[2] ? t[2].trim().replace(this.rules.inline.anyPunctuation, "$1") : t[2],
				text: n
			};
		}
	}
	heading(e) {
		let t = this.rules.block.heading.exec(e);
		if (t) {
			let e = t[2].trim();
			if (this.rules.other.endingHash.test(e)) {
				let t = q(e, "#");
				(this.options.pedantic || !t || this.rules.other.endingSpaceChar.test(t)) && (e = t.trim());
			}
			return {
				type: "heading",
				raw: q(t[0], "\n"),
				depth: t[1].length,
				text: e,
				tokens: this.lexer.inline(e)
			};
		}
	}
	hr(e) {
		let t = this.rules.block.hr.exec(e);
		if (t) return {
			type: "hr",
			raw: q(t[0], "\n")
		};
	}
	blockquote(e) {
		let t = this.rules.block.blockquote.exec(e);
		if (t) {
			let e = q(t[0], "\n").split("\n"), n = "", r = "", i = [];
			for (; e.length > 0;) {
				let t = !1, a = [], o;
				for (o = 0; o < e.length; o++) if (this.rules.other.blockquoteStart.test(e[o])) a.push(e[o]), t = !0;
				else if (!t) a.push(e[o]);
				else break;
				e = e.slice(o);
				let s = a.join("\n"), c = s.replace(this.rules.other.blockquoteSetextReplace, "\n    $1").replace(this.rules.other.blockquoteSetextReplace2, "");
				n = n ? `${n}
${s}` : s, r = r ? `${r}
${c}` : c;
				let l = this.lexer.state.top;
				if (this.lexer.state.top = !0, this.lexer.blockTokens(c, i, !0), this.lexer.state.top = l, e.length === 0) break;
				let u = i.at(-1);
				if ((u == null ? void 0 : u.type) === "code") break;
				if ((u == null ? void 0 : u.type) === "blockquote") {
					let t = u, a = e.join("\n"), o = t.raw + "\n" + a.replace(this.rules.other.blockquoteSetextReplace2, ""), s = this.blockquote(o);
					i[i.length - 1] = s, n = `${n}
${a}`, r = r.substring(0, r.length - t.text.length) + s.text;
					break;
				}
				if ((u == null ? void 0 : u.type) === "list") {
					let t = u, a = t.raw + "\n" + e.join("\n"), o = this.list(a);
					i[i.length - 1] = o, n = n.substring(0, n.length - u.raw.length) + o.raw, r = r.substring(0, r.length - t.raw.length) + o.raw, e = a.substring(i.at(-1).raw.length).split("\n");
					continue;
				}
			}
			return {
				type: "blockquote",
				raw: n,
				tokens: i,
				text: r
			};
		}
	}
	list(e) {
		let t = this.rules.block.list.exec(e);
		if (t) {
			let n = t[1].trim(), r = n.length > 1, i = {
				type: "list",
				raw: "",
				ordered: r,
				start: r ? +n.slice(0, -1) : "",
				loose: !1,
				items: []
			};
			n = r ? `\\d{1,9}\\${n.slice(-1)}` : `\\${n}`, this.options.pedantic && (n = r ? n : "[*+-]");
			let a = this.rules.other.listItemRegex(n), o = !1;
			for (; e;) {
				let n = !1, r = "", s = "";
				if (!(t = a.exec(e)) || this.rules.block.hr.test(e)) break;
				r = t[0], e = e.substring(r.length);
				let c = hn(t[2].split("\n", 1)[0], t[1].length), l = e.split("\n", 1)[0], u = !c.trim(), d = 0;
				if (this.options.pedantic ? (d = 2, s = c.trimStart()) : u ? d = t[1].length + 1 : (d = c.search(this.rules.other.nonSpaceChar), d = d > 4 ? 1 : d, s = c.slice(d), d += t[1].length), u && this.rules.other.blankLine.test(l) && (r += l + "\n", e = e.substring(l.length + 1), n = !0), !n) {
					let t = this.rules.other.nextBulletRegex(d), n = this.rules.other.hrRegex(d), i = this.rules.other.fencesBeginRegex(d), a = this.rules.other.headingBeginRegex(d), o = this.rules.other.htmlBeginRegex(d), f = this.rules.other.blockquoteBeginRegex(d);
					for (; e;) {
						let p = e.split("\n", 1)[0], m;
						if (l = p, this.options.pedantic ? (l = l.replace(this.rules.other.listReplaceNesting, "  "), m = l) : m = l.replace(this.rules.other.tabCharGlobal, "    "), i.test(l) || a.test(l) || o.test(l) || f.test(l) || t.test(l) || n.test(l)) break;
						if (m.search(this.rules.other.nonSpaceChar) >= d || !l.trim()) s += "\n" + m.slice(d);
						else {
							if (u || c.replace(this.rules.other.tabCharGlobal, "    ").search(this.rules.other.nonSpaceChar) >= 4 || i.test(c) || a.test(c) || n.test(c)) break;
							s += "\n" + l;
						}
						u = !l.trim(), r += p + "\n", e = e.substring(p.length + 1), c = m.slice(d);
					}
				}
				i.loose || (o ? i.loose = !0 : this.rules.other.doubleBlankLine.test(r) && (o = !0)), i.items.push({
					type: "list_item",
					raw: r,
					task: !!this.options.gfm && this.rules.other.listIsTask.test(s),
					loose: !1,
					text: s,
					tokens: []
				}), i.raw += r;
			}
			let s = i.items.at(-1);
			if (s) s.raw = s.raw.trimEnd(), s.text = s.text.trimEnd();
			else return;
			i.raw = i.raw.trimEnd();
			for (let e of i.items) if (this.lexer.state.top = !1, e.tokens = this.lexer.blockTokens(e.text, []), !i.loose) {
				let t = e.tokens.filter((e) => e.type === "space");
				i.loose = t.length > 0 && t.some((e) => this.rules.other.anyLine.test(e.raw));
			}
			for (let e of i.items) {
				let t = e.tokens[0];
				if (e.task && ((t == null ? void 0 : t.type) === "text" || (t == null ? void 0 : t.type) === "paragraph")) {
					e.text = e.text.replace(this.rules.other.listReplaceTask, ""), t.raw = t.raw.replace(this.rules.other.listReplaceTask, ""), t.text = t.text.replace(this.rules.other.listReplaceTask, "");
					for (let e = this.lexer.inlineQueue.length - 1; e >= 0; e--) if (this.rules.other.listIsTask.test(this.lexer.inlineQueue[e].src)) {
						this.lexer.inlineQueue[e].src = this.lexer.inlineQueue[e].src.replace(this.rules.other.listReplaceTask, "");
						break;
					}
					let n = this.rules.other.listTaskCheckbox.exec(e.raw);
					if (n) {
						let t = {
							type: "checkbox",
							raw: n[0] + " ",
							checked: n[0] !== "[ ]"
						};
						e.checked = t.checked, i.loose ? e.tokens[0] && ["paragraph", "text"].includes(e.tokens[0].type) && "tokens" in e.tokens[0] && e.tokens[0].tokens ? (e.tokens[0].raw = t.raw + e.tokens[0].raw, e.tokens[0].text = t.raw + e.tokens[0].text, e.tokens[0].tokens.unshift(t)) : e.tokens.unshift({
							type: "paragraph",
							raw: t.raw,
							text: t.raw,
							tokens: [t]
						}) : e.tokens.unshift(t);
					}
				} else e.task && (e.task = !1);
			}
			if (i.loose) for (let e of i.items) {
				e.loose = !0;
				for (let t of e.tokens) t.type === "text" && (t.type = "paragraph");
			}
			return i;
		}
	}
	html(e) {
		let t = this.rules.block.html.exec(e);
		if (t) {
			let e = J(t[0]);
			return {
				type: "html",
				block: !0,
				raw: e,
				pre: t[1] === "pre" || t[1] === "script" || t[1] === "style",
				text: e
			};
		}
	}
	def(e) {
		let t = this.rules.block.def.exec(e);
		if (t) {
			let e = t[1].toLowerCase().replace(this.rules.other.multipleSpaceGlobal, " "), n = t[2] ? t[2].replace(this.rules.other.hrefBrackets, "$1").replace(this.rules.inline.anyPunctuation, "$1") : "", r = t[3] ? t[3].substring(1, t[3].length - 1).replace(this.rules.inline.anyPunctuation, "$1") : t[3];
			return {
				type: "def",
				tag: e,
				raw: q(t[0], "\n"),
				href: n,
				title: r
			};
		}
	}
	table(e) {
		var t;
		let n = this.rules.block.table.exec(e);
		if (!n || !this.rules.other.tableDelimiter.test(n[2])) return;
		let r = pn(n[1]), i = n[2].replace(this.rules.other.tableAlignChars, "").split("|"), a = (t = n[3]) != null && t.trim() ? n[3].replace(this.rules.other.tableRowBlankLine, "").split("\n") : [], o = {
			type: "table",
			raw: q(n[0], "\n"),
			header: [],
			align: [],
			rows: []
		};
		if (r.length === i.length) {
			for (let e of i) this.rules.other.tableAlignRight.test(e) ? o.align.push("right") : this.rules.other.tableAlignCenter.test(e) ? o.align.push("center") : this.rules.other.tableAlignLeft.test(e) ? o.align.push("left") : o.align.push(null);
			for (let e = 0; e < r.length; e++) o.header.push({
				text: r[e],
				tokens: this.lexer.inline(r[e]),
				header: !0,
				align: o.align[e]
			});
			for (let e of a) o.rows.push(pn(e, o.header.length).map((e, t) => ({
				text: e,
				tokens: this.lexer.inline(e),
				header: !1,
				align: o.align[t]
			})));
			return o;
		}
	}
	lheading(e) {
		let t = this.rules.block.lheading.exec(e);
		if (t) {
			let e = t[1].trim();
			return {
				type: "heading",
				raw: q(t[0], "\n"),
				depth: t[2].charAt(0) === "=" ? 1 : 2,
				text: e,
				tokens: this.lexer.inline(e)
			};
		}
	}
	paragraph(e) {
		let t = this.rules.block.paragraph.exec(e);
		if (t) {
			let e = t[1].charAt(t[1].length - 1) === "\n" ? t[1].slice(0, -1) : t[1];
			return {
				type: "paragraph",
				raw: t[0],
				text: e,
				tokens: this.lexer.inline(e)
			};
		}
	}
	text(e) {
		let t = this.rules.block.text.exec(e);
		if (t) return {
			type: "text",
			raw: t[0],
			text: t[0],
			tokens: this.lexer.inline(t[0])
		};
	}
	escape(e) {
		let t = this.rules.inline.escape.exec(e);
		if (t) return {
			type: "escape",
			raw: t[0],
			text: t[1]
		};
	}
	tag(e) {
		let t = this.rules.inline.tag.exec(e);
		if (t) return !this.lexer.state.inLink && this.rules.other.startATag.test(t[0]) ? this.lexer.state.inLink = !0 : this.lexer.state.inLink && this.rules.other.endATag.test(t[0]) && (this.lexer.state.inLink = !1), !this.lexer.state.inRawBlock && this.rules.other.startPreScriptTag.test(t[0]) ? this.lexer.state.inRawBlock = !0 : this.lexer.state.inRawBlock && this.rules.other.endPreScriptTag.test(t[0]) && (this.lexer.state.inRawBlock = !1), {
			type: "html",
			raw: t[0],
			inLink: this.lexer.state.inLink,
			inRawBlock: this.lexer.state.inRawBlock,
			block: !1,
			text: t[0]
		};
	}
	link(e) {
		let t = this.rules.inline.link.exec(e);
		if (t) {
			let e = t[2].trim();
			if (!this.options.pedantic && this.rules.other.startAngleBracket.test(e)) {
				if (!this.rules.other.endAngleBracket.test(e)) return;
				let t = q(e.slice(0, -1), "\\");
				if ((e.length - t.length) % 2 == 0) return;
			} else {
				let e = mn(t[2], "()");
				if (e === -2) return;
				if (e > -1) {
					let n = (t[0].indexOf("!") === 0 ? 5 : 4) + t[1].length + e;
					t[2] = t[2].substring(0, e), t[0] = t[0].substring(0, n).trim(), t[3] = "";
				}
			}
			let n = t[2], r = "";
			if (this.options.pedantic) {
				let e = this.rules.other.pedanticHrefTitle.exec(n);
				e && (n = e[1], r = e[3]);
			} else r = t[3] ? t[3].slice(1, -1) : "";
			return n = n.trim(), this.rules.other.startAngleBracket.test(n) && (n = this.options.pedantic && !this.rules.other.endAngleBracket.test(e) ? n.slice(1) : n.slice(1, -1)), gn(t, {
				href: n && n.replace(this.rules.inline.anyPunctuation, "$1"),
				title: r && r.replace(this.rules.inline.anyPunctuation, "$1")
			}, t[0], this.lexer, this.rules);
		}
	}
	reflink(e, t) {
		let n;
		if ((n = this.rules.inline.reflink.exec(e)) || (n = this.rules.inline.nolink.exec(e))) {
			let e = t[(n[2] || n[1]).replace(this.rules.other.multipleSpaceGlobal, " ").toLowerCase()];
			if (!e) {
				let e = n[0].charAt(0);
				return {
					type: "text",
					raw: e,
					text: e
				};
			}
			return gn(n, e, n[0], this.lexer, this.rules);
		}
	}
	emStrong(e, t, n = "") {
		let r = this.rules.inline.emStrongLDelim.exec(e);
		if (!(!r || !r[1] && !r[2] && !r[3] && !r[4] || r[4] && n.match(this.rules.other.unicodeAlphaNumeric)) && (!(r[1] || r[3]) || !n || this.rules.inline.punctuation.exec(n))) {
			let i = [...r[0]].length - 1, a, o, s = i, c = 0, l = r[0][0], u = n === l, d = l === "*" ? this.rules.inline.emStrongRDelimAst : this.rules.inline.emStrongRDelimUnd;
			for (d.lastIndex = 0, t = t.slice(-1 * e.length + i); (r = d.exec(t)) !== null;) {
				if (a = r[1] || r[2] || r[3] || r[4] || r[5] || r[6], !a) continue;
				if (o = [...a].length, r[3] || r[4]) {
					s += o;
					continue;
				}
				if (r[5] || r[6]) {
					if (i % 3 && !((i + o) % 3)) {
						c += o;
						continue;
					}
					if (u) break;
				}
				if (s -= o, s > 0) continue;
				o = Math.min(o, o + s + c);
				let t = [...r[0]][0].length, n = e.slice(0, i + r.index + t + o);
				if (Math.min(i, o) % 2) {
					let e = n.slice(1, -1);
					return {
						type: "em",
						raw: n,
						text: e,
						tokens: this.lexer.inlineTokens(e)
					};
				}
				let l = n.slice(2, -2);
				return {
					type: "strong",
					raw: n,
					text: l,
					tokens: this.lexer.inlineTokens(l)
				};
			}
		}
	}
	codespan(e) {
		let t = this.rules.inline.code.exec(e);
		if (t) {
			let e = t[2].replace(this.rules.other.newLineCharGlobal, " "), n = this.rules.other.nonSpaceChar.test(e), r = this.rules.other.startingSpaceChar.test(e) && this.rules.other.endingSpaceChar.test(e);
			return n && r && (e = e.substring(1, e.length - 1)), {
				type: "codespan",
				raw: t[0],
				text: e
			};
		}
	}
	br(e) {
		let t = this.rules.inline.br.exec(e);
		if (t) return {
			type: "br",
			raw: t[0]
		};
	}
	del(e, t, n = "") {
		let r = this.rules.inline.delLDelim.exec(e);
		if (r && (!r[1] || !n || this.rules.inline.punctuation.exec(n))) {
			let n = [...r[0]].length - 1, i, a, o = n, s = this.rules.inline.delRDelim;
			for (s.lastIndex = 0, t = t.slice(-1 * e.length + n); (r = s.exec(t)) !== null;) {
				if (i = r[1] || r[2] || r[3] || r[4] || r[5] || r[6], !i || (a = [...i].length, a !== n)) continue;
				if (r[3] || r[4]) {
					o += a;
					continue;
				}
				if (o -= a, o > 0) continue;
				a = Math.min(a, a + o);
				let t = [...r[0]][0].length, s = e.slice(0, n + r.index + t + a), c = s.slice(n, -n);
				return {
					type: "del",
					raw: s,
					text: c,
					tokens: this.lexer.inlineTokens(c)
				};
			}
		}
	}
	autolink(e) {
		let t = this.rules.inline.autolink.exec(e);
		if (t) {
			let e, n;
			return t[2] === "@" ? (e = t[1], n = "mailto:" + e) : (e = t[1], n = e), {
				type: "link",
				raw: t[0],
				text: e,
				href: n,
				tokens: [{
					type: "text",
					raw: e,
					text: e
				}]
			};
		}
	}
	url(e) {
		let t;
		if (t = this.rules.inline.url.exec(e)) {
			let e, i;
			if (t[2] === "@") e = t[0], i = "mailto:" + e;
			else {
				var n, r;
				let a;
				do
					a = t[0], t[0] = (n = (r = this.rules.inline._backpedal.exec(t[0])) == null ? void 0 : r[0]) == null ? "" : n;
				while (a !== t[0]);
				e = t[0], i = t[1] === "www." ? "http://" + t[0] : t[0];
			}
			return {
				type: "link",
				raw: t[0],
				text: e,
				href: i,
				tokens: [{
					type: "text",
					raw: e,
					text: e
				}]
			};
		}
	}
	inlineText(e) {
		let t = this.rules.inline.text.exec(e);
		if (t) {
			let e = this.lexer.state.inRawBlock;
			return {
				type: "text",
				raw: t[0],
				text: t[0],
				escaped: e
			};
		}
	}
}, Y = class e {
	constructor(e) {
		D(this, "tokens", void 0), D(this, "options", void 0), D(this, "state", void 0), D(this, "inlineQueue", void 0), D(this, "tokenizer", void 0), this.tokens = [], this.tokens.links = Object.create(null), this.options = e || A, this.options.tokenizer = this.options.tokenizer || new vn(), this.tokenizer = this.options.tokenizer, this.tokenizer.options = this.options, this.tokenizer.lexer = this, this.inlineQueue = [], this.state = {
			inLink: !1,
			inRawBlock: !1,
			linkEmitted: !1,
			top: !0
		};
		let t = {
			other: N,
			block: ln.normal,
			inline: un.normal
		};
		this.options.pedantic ? (t.block = ln.pedantic, t.inline = un.pedantic) : this.options.gfm && (t.block = ln.gfm, t.inline = this.options.breaks ? un.breaks : un.gfm), this.tokenizer.rules = t;
	}
	static get rules() {
		return {
			block: ln,
			inline: un
		};
	}
	static lex(t, n) {
		return new e(n).lex(t);
	}
	static lexInline(t, n) {
		return new e(n).inlineTokens(t);
	}
	lex(e) {
		e = e.replace(N.carriageReturn, "\n"), this.blockTokens(e, this.tokens);
		for (let e = 0; e < this.inlineQueue.length; e++) {
			let t = this.inlineQueue[e];
			this.inlineTokens(t.src, t.tokens);
		}
		return this.inlineQueue = [], this.tokens;
	}
	blockTokens(e, t = [], n = !1) {
		this.tokenizer.lexer = this, this.options.pedantic && (e = e.replace(N.tabCharGlobal, "    ").replace(N.spaceLine, ""));
		let r = 1 / 0;
		for (; e;) {
			var i, a;
			if (e.length < r) r = e.length;
			else {
				this.infiniteLoopError(e.charCodeAt(0));
				break;
			}
			let o;
			if ((i = this.options.extensions) != null && (i = i.block) != null && i.some((n) => (o = n.call({ lexer: this }, e, t)) ? (e = e.substring(o.raw.length), t.push(o), !0) : !1)) continue;
			if (o = this.tokenizer.space(e)) {
				e = e.substring(o.raw.length);
				let n = t.at(-1);
				o.raw.length === 1 && n !== void 0 ? n.raw += "\n" : t.push(o);
				continue;
			}
			if (o = this.tokenizer.code(e)) {
				e = e.substring(o.raw.length);
				let n = t.at(-1);
				(n == null ? void 0 : n.type) === "paragraph" || (n == null ? void 0 : n.type) === "text" ? (n.raw += (n.raw.endsWith("\n") ? "" : "\n") + o.raw, n.text += "\n" + o.text, this.inlineQueue.at(-1).src = n.text) : t.push(o);
				continue;
			}
			if (o = this.tokenizer.fences(e)) {
				e = e.substring(o.raw.length), t.push(o);
				continue;
			}
			if (o = this.tokenizer.heading(e)) {
				e = e.substring(o.raw.length), t.push(o);
				continue;
			}
			if (o = this.tokenizer.hr(e)) {
				e = e.substring(o.raw.length), t.push(o);
				continue;
			}
			if (o = this.tokenizer.blockquote(e)) {
				e = e.substring(o.raw.length), t.push(o);
				continue;
			}
			if (o = this.tokenizer.list(e)) {
				e = e.substring(o.raw.length), t.push(o);
				continue;
			}
			if (o = this.tokenizer.html(e)) {
				e = e.substring(o.raw.length), t.push(o);
				continue;
			}
			if (o = this.tokenizer.def(e)) {
				e = e.substring(o.raw.length);
				let n = t.at(-1);
				(n == null ? void 0 : n.type) === "paragraph" || (n == null ? void 0 : n.type) === "text" ? (n.raw += (n.raw.endsWith("\n") ? "" : "\n") + o.raw, n.text += "\n" + o.raw, this.inlineQueue.at(-1).src = n.text) : this.tokens.links[o.tag] || (this.tokens.links[o.tag] = {
					href: o.href,
					title: o.title
				}, t.push(o));
				continue;
			}
			if (o = this.tokenizer.table(e)) {
				e = e.substring(o.raw.length), t.push(o);
				continue;
			}
			if (o = this.tokenizer.lheading(e)) {
				e = e.substring(o.raw.length), t.push(o);
				continue;
			}
			let s = e;
			if ((a = this.options.extensions) != null && a.startBlock) {
				let t = 1 / 0, n = e.slice(1), r;
				this.options.extensions.startBlock.forEach((e) => {
					r = e.call({ lexer: this }, n), typeof r == "number" && r >= 0 && (t = Math.min(t, r));
				}), t < 1 / 0 && t >= 0 && (s = e.substring(0, t + 1));
			}
			if (this.state.top && (o = this.tokenizer.paragraph(s))) {
				let r = t.at(-1);
				n && (r == null ? void 0 : r.type) === "paragraph" ? (r.raw += (r.raw.endsWith("\n") ? "" : "\n") + o.raw, r.text += "\n" + o.text, this.inlineQueue.pop(), this.inlineQueue.at(-1).src = r.text) : t.push(o), n = s.length !== e.length, e = e.substring(o.raw.length);
				continue;
			}
			if (o = this.tokenizer.text(e)) {
				e = e.substring(o.raw.length);
				let n = t.at(-1);
				(n == null ? void 0 : n.type) === "text" ? (n.raw += (n.raw.endsWith("\n") ? "" : "\n") + o.raw, n.text += "\n" + o.text, this.inlineQueue.pop(), this.inlineQueue.at(-1).src = n.text) : t.push(o);
				continue;
			}
			if (e) {
				this.infiniteLoopError(e.charCodeAt(0));
				break;
			}
		}
		return this.state.top = !0, t;
	}
	inline(e, t = []) {
		return this.inlineQueue.push({
			src: e,
			tokens: t
		}), t;
	}
	linkInText(e) {
		if (!e.includes("[")) return !1;
		let t = this.tokenizer.rules.inline.link;
		for (let n of e.matchAll(this.tokenizer.rules.inline.blockSkip)) if (t.test(n[0]) && e.charAt(n.index - 1) !== "!") return !0;
		for (let t of e.matchAll(this.tokenizer.rules.inline.reflinkSearch)) {
			let e = t[0], n = e.lastIndexOf("[");
			if (!(e.charAt(0) === "!" || !Object.hasOwn(this.tokens.links, e.slice(n + 1, -1))) && !(n > 1 && this.linkInText(e.slice(1, n - 1)))) return !0;
		}
		return !1;
	}
	inlineTokens(e, t = []) {
		var n, r;
		this.tokenizer.lexer = this;
		let i = e;
		if (this.tokens.links && e.includes("[")) {
			let e = this.tokenizer.rules.inline.reflinkSearch, t = (n) => {
				let r = n.lastIndexOf("[");
				if (!Object.hasOwn(this.tokens.links, n.slice(r + 1, -1))) return n;
				if (r > 1 && n.charAt(0) !== "!") {
					let i = n.slice(1, r - 1);
					if (this.linkInText(i)) return "[" + i.replace(e, t) + "][" + "a".repeat(n.length - r - 2) + "]";
				}
				return "[" + "a".repeat(n.length - 2) + "]";
			};
			i = i.replace(e, t);
		}
		i = i.replace(this.tokenizer.rules.inline.anyPunctuation, (e) => "+".repeat(e.length)), i = i.replace(this.tokenizer.rules.inline.blockSkip, (e, t, n) => {
			let r = n ? n.length : 0;
			return e.slice(0, r) + "[" + "a".repeat(e.length - r - 2) + "]";
		}), i = (n = (r = this.options.hooks) == null || (r = r.emStrongMask) == null ? void 0 : r.call({ lexer: this }, i)) == null ? i : n;
		let a = !1, o = "", s = 1 / 0;
		for (; e;) {
			var c, l;
			if (e.length < s) s = e.length;
			else {
				this.infiniteLoopError(e.charCodeAt(0));
				break;
			}
			a || (o = ""), a = !1;
			let n;
			if ((c = this.options.extensions) != null && (c = c.inline) != null && c.some((r) => (n = r.call({ lexer: this }, e, t)) ? (e = e.substring(n.raw.length), t.push(n), !0) : !1)) continue;
			if (n = this.tokenizer.escape(e)) {
				e = e.substring(n.raw.length), t.push(n);
				continue;
			}
			if (n = this.tokenizer.tag(e)) {
				e = e.substring(n.raw.length), t.push(n);
				continue;
			}
			if (n = this.tokenizer.link(e)) {
				e = e.substring(n.raw.length), t.push(n);
				continue;
			}
			if (n = this.tokenizer.reflink(e, this.tokens.links)) {
				e = e.substring(n.raw.length);
				let r = t.at(-1);
				n.type === "text" && (r == null ? void 0 : r.type) === "text" ? (r.raw += n.raw, r.text += n.text) : t.push(n);
				continue;
			}
			if (n = this.tokenizer.emStrong(e, i, o)) {
				e = e.substring(n.raw.length), t.push(n);
				continue;
			}
			if (n = this.tokenizer.codespan(e)) {
				e = e.substring(n.raw.length), t.push(n);
				continue;
			}
			if (n = this.tokenizer.br(e)) {
				e = e.substring(n.raw.length), t.push(n);
				continue;
			}
			if (n = this.tokenizer.del(e, i, o)) {
				e = e.substring(n.raw.length), t.push(n);
				continue;
			}
			if (n = this.tokenizer.autolink(e)) {
				e = e.substring(n.raw.length), t.push(n);
				continue;
			}
			if (!this.state.inLink && (n = this.tokenizer.url(e))) {
				e = e.substring(n.raw.length), t.push(n);
				continue;
			}
			let r = e;
			if ((l = this.options.extensions) != null && l.startInline) {
				let t = 1 / 0, n = e.slice(1), i;
				this.options.extensions.startInline.forEach((e) => {
					i = e.call({ lexer: this }, n), typeof i == "number" && i >= 0 && (t = Math.min(t, i));
				}), t < 1 / 0 && t >= 0 && (r = e.substring(0, t + 1));
			}
			if (n = this.tokenizer.inlineText(r)) {
				e = e.substring(n.raw.length), n.raw.slice(-1) !== "_" && (o = n.raw.slice(-1)), a = !0;
				let r = t.at(-1);
				(r == null ? void 0 : r.type) === "text" ? (r.raw += n.raw, r.text += n.text) : t.push(n);
				continue;
			}
			if (e) {
				this.infiniteLoopError(e.charCodeAt(0));
				break;
			}
		}
		return t;
	}
	infiniteLoopError(e) {
		let t = "Infinite loop on byte: " + e;
		if (this.options.silent) console.error(t);
		else throw Error(t);
	}
}, yn = class {
	constructor(e) {
		D(this, "options", void 0), D(this, "parser", void 0), this.options = e || A;
	}
	space(e) {
		return "";
	}
	code({ text: e, lang: t, escaped: n }) {
		var r;
		let i = (r = (t || "").match(N.notSpaceStart)) == null ? void 0 : r[0], a = e.replace(N.endingNewline, "") + "\n";
		return i ? "<pre><code class=\"language-" + G(i) + "\">" + (n ? a : G(a, !0)) + "</code></pre>\n" : "<pre><code>" + (n ? a : G(a, !0)) + "</code></pre>\n";
	}
	blockquote({ tokens: e }) {
		return `<blockquote>
${this.parser.parse(e)}</blockquote>
`;
	}
	html({ text: e }) {
		return e;
	}
	def(e) {
		return "";
	}
	heading({ tokens: e, depth: t }) {
		return `<h${t}>${this.parser.parseInline(e)}</h${t}>
`;
	}
	hr(e) {
		return "<hr>\n";
	}
	list(e) {
		let t = e.ordered, n = e.start, r = "";
		for (let t = 0; t < e.items.length; t++) {
			let n = e.items[t];
			r += this.listitem(n);
		}
		let i = t ? "ol" : "ul", a = t && n !== 1 ? " start=\"" + n + "\"" : "";
		return "<" + i + a + ">\n" + r + "</" + i + ">\n";
	}
	listitem(e) {
		return `<li>${this.parser.parse(e.tokens)}</li>
`;
	}
	checkbox({ checked: e }) {
		return "<input " + (e ? "checked=\"\" " : "") + "disabled=\"\" type=\"checkbox\"> ";
	}
	paragraph({ tokens: e }) {
		return `<p>${this.parser.parseInline(e)}</p>
`;
	}
	table(e) {
		let t = "", n = "";
		for (let t = 0; t < e.header.length; t++) n += this.tablecell(e.header[t]);
		t += this.tablerow({ text: n });
		let r = "";
		for (let t = 0; t < e.rows.length; t++) {
			let i = e.rows[t];
			n = "";
			for (let e = 0; e < i.length; e++) n += this.tablecell(i[e]);
			r += this.tablerow({ text: n });
		}
		return r && (r = `<tbody>${r}</tbody>`), "<table>\n<thead>\n" + t + "</thead>\n" + r + "</table>\n";
	}
	tablerow({ text: e }) {
		return `<tr>
${e}</tr>
`;
	}
	tablecell(e) {
		let t = this.parser.parseInline(e.tokens), n = e.header ? "th" : "td";
		return (e.align ? `<${n} align="${e.align}">` : `<${n}>`) + t + `</${n}>
`;
	}
	strong({ tokens: e }) {
		return `<strong>${this.parser.parseInline(e)}</strong>`;
	}
	em({ tokens: e }) {
		return `<em>${this.parser.parseInline(e)}</em>`;
	}
	codespan({ text: e }) {
		return `<code>${G(e, !0)}</code>`;
	}
	br(e) {
		return "<br>";
	}
	del({ tokens: e }) {
		return `<del>${this.parser.parseInline(e)}</del>`;
	}
	link({ href: e, title: t, tokens: n }) {
		let r = this.parser.parseInline(n), i = K(e);
		if (i === null) return r;
		e = i;
		let a = "<a href=\"" + e + "\"";
		return t && (a += " title=\"" + G(t) + "\""), a += ">" + r + "</a>", a;
	}
	image({ href: e, title: t, text: n, tokens: r }) {
		r && (n = this.parser.parseInline(r, this.parser.textRenderer));
		let i = K(e);
		if (i === null) return G(n);
		e = i;
		let a = `<img src="${e}" alt="${G(n)}"`;
		return t && (a += ` title="${G(t)}"`), a += ">", a;
	}
	text(e) {
		return "tokens" in e && e.tokens ? this.parser.parseInline(e.tokens) : "escaped" in e && e.escaped ? e.text : G(e.text);
	}
}, bn = class {
	strong({ text: e }) {
		return e;
	}
	em({ text: e }) {
		return e;
	}
	codespan({ text: e }) {
		return e;
	}
	del({ text: e }) {
		return e;
	}
	html({ text: e }) {
		return e;
	}
	text({ text: e }) {
		return e;
	}
	link({ text: e }) {
		return "" + e;
	}
	image({ text: e }) {
		return "" + e;
	}
	br() {
		return "";
	}
	checkbox({ raw: e }) {
		return e;
	}
}, X = class e {
	constructor(e) {
		D(this, "options", void 0), D(this, "renderer", void 0), D(this, "textRenderer", void 0), this.options = e || A, this.options.renderer = this.options.renderer || new yn(), this.renderer = this.options.renderer, this.renderer.options = this.options, this.renderer.parser = this, this.textRenderer = new bn();
	}
	static parse(t, n) {
		return new e(n).parse(t);
	}
	static parseInline(t, n) {
		return new e(n).parseInline(t);
	}
	parse(e) {
		this.renderer.parser = this;
		let t = "";
		for (let r = 0; r < e.length; r++) {
			var n;
			let i = e[r];
			if ((n = this.options.extensions) != null && (n = n.renderers) != null && n[i.type]) {
				let e = i, n = this.options.extensions.renderers[e.type].call({ parser: this }, e);
				if (n !== !1 || ![
					"space",
					"hr",
					"heading",
					"code",
					"table",
					"blockquote",
					"list",
					"checkbox",
					"html",
					"def",
					"paragraph",
					"text"
				].includes(e.type)) {
					t += n || "";
					continue;
				}
			}
			let a = i;
			switch (a.type) {
				case "space":
					t += this.renderer.space(a);
					break;
				case "hr":
					t += this.renderer.hr(a);
					break;
				case "heading":
					t += this.renderer.heading(a);
					break;
				case "code":
					t += this.renderer.code(a);
					break;
				case "table":
					t += this.renderer.table(a);
					break;
				case "blockquote":
					t += this.renderer.blockquote(a);
					break;
				case "list":
					t += this.renderer.list(a);
					break;
				case "checkbox":
					t += this.renderer.checkbox(a);
					break;
				case "html":
					t += this.renderer.html(a);
					break;
				case "def":
					t += this.renderer.def(a);
					break;
				case "paragraph":
					t += this.renderer.paragraph(a);
					break;
				case "text":
					t += this.renderer.text(a);
					break;
				default: {
					let e = "Token with \"" + a.type + "\" type was not found.";
					if (this.options.silent) return console.error(e), "";
					throw Error(e);
				}
			}
		}
		return t;
	}
	parseInline(e, t = this.renderer) {
		this.renderer.parser = this;
		let n = "";
		for (let i = 0; i < e.length; i++) {
			var r;
			let a = e[i];
			if ((r = this.options.extensions) != null && (r = r.renderers) != null && r[a.type]) {
				let e = this.options.extensions.renderers[a.type].call({ parser: this }, a);
				if (e !== !1 || ![
					"escape",
					"html",
					"link",
					"image",
					"checkbox",
					"strong",
					"em",
					"codespan",
					"br",
					"del",
					"text"
				].includes(a.type)) {
					n += e || "";
					continue;
				}
			}
			let o = a;
			switch (o.type) {
				case "escape":
					n += t.text(o);
					break;
				case "html":
					n += t.html(o);
					break;
				case "link":
					n += t.link(o);
					break;
				case "image":
					n += t.image(o);
					break;
				case "checkbox":
					n += t.checkbox(o);
					break;
				case "strong":
					n += t.strong(o);
					break;
				case "em":
					n += t.em(o);
					break;
				case "codespan":
					n += t.codespan(o);
					break;
				case "br":
					n += t.br(o);
					break;
				case "del":
					n += t.del(o);
					break;
				case "text":
					n += t.text(o);
					break;
				default: {
					let e = "Token with \"" + o.type + "\" type was not found.";
					if (this.options.silent) return console.error(e), "";
					throw Error(e);
				}
			}
		}
		return n;
	}
}, Z = (at = class {
	constructor(e) {
		D(this, "options", void 0), D(this, "block", void 0), this.options = e || A;
	}
	preprocess(e) {
		return e;
	}
	postprocess(e) {
		return e;
	}
	processAllTokens(e) {
		return e;
	}
	emStrongMask(e) {
		return e;
	}
	provideLexer(e = this.block) {
		return e ? Y.lex : Y.lexInline;
	}
	provideParser(e = this.block) {
		return e ? X.parse : X.parseInline;
	}
}, D(at, "passThroughHooks", /* @__PURE__ */ new Set([
	"preprocess",
	"postprocess",
	"processAllTokens",
	"emStrongMask"
])), D(at, "passThroughHooksRespectAsync", /* @__PURE__ */ new Set([
	"preprocess",
	"postprocess",
	"processAllTokens"
])), at), Q = new class {
	constructor(...e) {
		D(this, "defaults", ot()), D(this, "options", this.setOptions), D(this, "parse", this.parseMarkdown(!0)), D(this, "parseInline", this.parseMarkdown(!1)), D(this, "Parser", X), D(this, "Renderer", yn), D(this, "TextRenderer", bn), D(this, "Lexer", Y), D(this, "Tokenizer", vn), D(this, "Hooks", Z), this.use(...e);
	}
	walkTokens(e, t) {
		let n = [];
		for (let i of e) switch (n = n.concat(t.call(this, i)), i.type) {
			case "table": {
				let e = i;
				for (let r of e.header) n = n.concat(this.walkTokens(r.tokens, t));
				for (let r of e.rows) for (let e of r) n = n.concat(this.walkTokens(e.tokens, t));
				break;
			}
			case "list": {
				let e = i;
				n = n.concat(this.walkTokens(e.items, t));
				break;
			}
			default: {
				var r;
				let e = i;
				(r = this.defaults.extensions) != null && (r = r.childTokens) != null && r[e.type] ? this.defaults.extensions.childTokens[e.type].forEach((r) => {
					let i = e[r].flat(1 / 0);
					n = n.concat(this.walkTokens(i, t));
				}) : e.tokens && (n = n.concat(this.walkTokens(e.tokens, t)));
			}
		}
		return n;
	}
	use(...e) {
		let t = this.defaults.extensions || {
			renderers: {},
			childTokens: {}
		};
		return e.forEach((e) => {
			let n = O({}, e);
			if (n.async = this.defaults.async || n.async || !1, e.extensions && (e.extensions.forEach((e) => {
				if (!e.name) throw Error("extension name required");
				if ("renderer" in e) {
					let n = t.renderers[e.name];
					n ? t.renderers[e.name] = function(...t) {
						let r = e.renderer.apply(this, t);
						return r === !1 && (r = n.apply(this, t)), r;
					} : t.renderers[e.name] = e.renderer;
				}
				if ("tokenizer" in e) {
					if (!e.level || e.level !== "block" && e.level !== "inline") throw Error("extension level must be 'block' or 'inline'");
					let n = t[e.level];
					n ? n.unshift(e.tokenizer) : t[e.level] = [e.tokenizer], e.start && (e.level === "block" ? t.startBlock ? t.startBlock.push(e.start) : t.startBlock = [e.start] : e.level === "inline" && (t.startInline ? t.startInline.push(e.start) : t.startInline = [e.start]));
				}
				"childTokens" in e && e.childTokens && (t.childTokens[e.name] = e.childTokens);
			}), n.extensions = t), e.renderer) {
				let t = this.defaults.renderer || new yn(this.defaults);
				for (let n in e.renderer) {
					if (!(n in t)) throw Error(`renderer '${n}' does not exist`);
					if (["options", "parser"].includes(n)) continue;
					let r = n, i = e.renderer[r], a = t[r];
					t[r] = (...e) => {
						let n = i.apply(t, e);
						return n === !1 && (n = a.apply(t, e)), n || "";
					};
				}
				n.renderer = t;
			}
			if (e.tokenizer) {
				let t = this.defaults.tokenizer || new vn(this.defaults);
				for (let n in e.tokenizer) {
					if (!(n in t)) throw Error(`tokenizer '${n}' does not exist`);
					if ([
						"options",
						"rules",
						"lexer"
					].includes(n)) continue;
					let r = n, i = e.tokenizer[r], a = t[r];
					t[r] = (...e) => {
						let n = i.apply(t, e);
						return n === !1 && (n = a.apply(t, e)), n;
					};
				}
				n.tokenizer = t;
			}
			if (e.hooks) {
				let t = this.defaults.hooks || new Z();
				for (let n in e.hooks) {
					if (!(n in t)) throw Error(`hook '${n}' does not exist`);
					if (["options", "block"].includes(n)) continue;
					let r = n, i = e.hooks[r], a = t[r];
					t[r] = Z.passThroughHooks.has(n) ? (e) => {
						if (this.defaults.async && Z.passThroughHooksRespectAsync.has(n)) return k(function* () {
							let n = yield i.call(t, e);
							return a.call(t, n);
						})();
						let r = i.call(t, e);
						return a.call(t, r);
					} : (...e) => {
						if (this.defaults.async) return k(function* () {
							let n = yield i.apply(t, e);
							return n === !1 && (n = yield a.apply(t, e)), n;
						})();
						let n = i.apply(t, e);
						return n === !1 && (n = a.apply(t, e)), n;
					};
				}
				n.hooks = t;
			}
			if (e.walkTokens) {
				let t = this.defaults.walkTokens, r = e.walkTokens;
				n.walkTokens = function(e) {
					let n = [];
					return n.push(r.call(this, e)), t && (n = n.concat(t.call(this, e))), n;
				};
			}
			this.defaults = O(O({}, this.defaults), n);
		}), this;
	}
	setOptions(e) {
		return this.defaults = O(O({}, this.defaults), e), this;
	}
	lexer(e, t) {
		return Y.lex(e, t == null ? this.defaults : t);
	}
	parser(e, t) {
		return X.parse(e, t == null ? this.defaults : t);
	}
	parseMarkdown(e) {
		var t = this;
		return (n, r) => {
			let i = O({}, r), a = O(O({}, this.defaults), i), o = this.onError(!!a.silent, !!a.async);
			if (this.defaults.async === !0 && i.async === !1) return o(/* @__PURE__ */ Error("marked(): The async option was set to true by an extension. Remove async: false from the parse options object to return a Promise."));
			if (typeof n > "u" || n === null) return o(/* @__PURE__ */ Error("marked(): input parameter is undefined or null"));
			if (typeof n != "string") return o(/* @__PURE__ */ Error("marked(): input parameter is of type " + Object.prototype.toString.call(n) + ", string expected"));
			if (a.hooks && (a.hooks.options = a, a.hooks.block = e), a.async) return k(function* () {
				let r = a.hooks ? yield a.hooks.preprocess(n) : n, i = yield (a.hooks ? yield a.hooks.provideLexer(e) : e ? Y.lex : Y.lexInline)(r, a), o = a.hooks ? yield a.hooks.processAllTokens(i) : i;
				a.walkTokens && (yield Promise.all(t.walkTokens(o, a.walkTokens)));
				let s = yield (a.hooks ? yield a.hooks.provideParser(e) : e ? X.parse : X.parseInline)(o, a);
				return a.hooks ? yield a.hooks.postprocess(s) : s;
			})().catch(o);
			try {
				a.hooks && (n = a.hooks.preprocess(n));
				let t = (a.hooks ? a.hooks.provideLexer(e) : e ? Y.lex : Y.lexInline)(n, a);
				a.hooks && (t = a.hooks.processAllTokens(t)), a.walkTokens && this.walkTokens(t, a.walkTokens);
				let r = (a.hooks ? a.hooks.provideParser(e) : e ? X.parse : X.parseInline)(t, a);
				return a.hooks && (r = a.hooks.postprocess(r)), r;
			} catch (e) {
				return o(e);
			}
		};
	}
	onError(e, t) {
		return (n) => {
			if (n.message += "\nPlease report this to https://github.com/markedjs/marked.", e) {
				let e = "<p>An error occurred:</p><pre>" + G(n.message + "", !0) + "</pre>";
				return t ? Promise.resolve(e) : e;
			}
			if (t) return Promise.reject(n);
			throw n;
		};
	}
}();
function $(e, t) {
	return Q.parse(e, t);
}
$.options = $.setOptions = function(e) {
	return Q.setOptions(e), $.defaults = Q.defaults, st($.defaults), $;
}, $.getDefaults = ot, $.defaults = A;
function xn(...e) {
	return Q.use(...e), $.defaults = Q.defaults, st($.defaults), $;
}
$.use = xn, $.walkTokens = function(e, t) {
	return Q.walkTokens(e, t);
}, $.parseInline = Q.parseInline, $.Parser = X, $.parser = X.parse, $.Renderer = yn, $.TextRenderer = bn, $.Lexer = Y, $.lexer = Y.lex, $.Tokenizer = vn, $.Hooks = Z, $.parse = $, $.options, $.setOptions, $.walkTokens, $.parseInline, X.parse, Y.lex;
//#endregion
//#region src/main.js
var Sn = {
	ALLOWED_TAGS: [
		"p",
		"br",
		"hr",
		"h1",
		"h2",
		"h3",
		"h4",
		"h5",
		"h6",
		"blockquote",
		"pre",
		"code",
		"ul",
		"ol",
		"li",
		"strong",
		"em",
		"del",
		"table",
		"thead",
		"tbody",
		"tr",
		"th",
		"td"
	],
	ALLOWED_ATTR: [],
	ALLOW_ARIA_ATTR: !1,
	ALLOW_DATA_ATTR: !1
};
function Cn(e, t = {}) {
	var n;
	let r = (n = t.content) == null ? e.textContent : n;
	return e.innerHTML = et.sanitize($.parse(r), Sn), e.dataset.markdownRendered = "true", e;
}
function wn(e = document) {
	return Array.from(e.querySelectorAll(".ail-markdown:not([data-markdown-rendered])"), (e) => Cn(e));
}
//#endregion
export { Cn as createMarkdownRenderer, wn as renderMarkdownElements };
