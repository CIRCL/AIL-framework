/* Lightweight, page-local MISP enrichment projection. No raw response storage. */
(function (host, factory) {
    'use strict';
    const api = factory();
    if (typeof module === 'object' && module.exports) {
        module.exports = api;
    }
    if (host) {
        host.AILMISPGraph = api;
    }
})(typeof window === 'undefined' ? null : window, function () {
    'use strict';

    class ConversionError extends Error {}

    const dataOf = element => element?.getData?.() || element?.data || {};
    const scalar = value => typeof value === 'string' || typeof value === 'number' && Number.isFinite(value);
    const metadataRelations = new Set(['title', 'language', 'comment', 'description', 'name', 'source', 'origin', 'count', 'counter', 'rrtype', 'rrname', 'rdata', 'filename', 'file-name', 'size-in-bytes', 'filesize', 'file-size', 'mimetype', 'mime-type', 'scheme', 'tld', 'subdomain', 'domain-without-tld', 'resource-path', 'query-string', 'fragment', 'port', 'issuer', 'subject', 'pubkey-info-size', 'validity-not-before', 'validity-not-after', 'knownmalicious']);
    const observableTypes = new Set(['domain', 'hostname', 'onion-address', 'ip', 'ip-src', 'ip-dst', 'url', 'uri', 'ssh-fingerprint', 'md5', 'sha1', 'sha256', 'sha512', 'ssdeep', 'tlsh', 'AS', 'email', 'email-src', 'email-dst', 'whois-registrant-email', 'x509-fingerprint-sha1', 'x509-fingerprint-sha256', 'domain|ip', 'ip-src|port', 'ip-dst|port', 'vulnerability', 'weakness', 'cpe']);
    const pgpObjects = new Set(['pgp-key', 'pgp-meta', 'pgp-sign']);
    const pgpRelations = {'key-id': 'pgp-key-id', 'issuer-key-id': 'pgp-key-id', fingerprint: 'pgp-fingerprint', 'key-fingerprint': 'pgp-fingerprint', 'issuer-fingerprint': 'pgp-fingerprint', 'subkey-fingerprint': 'pgp-fingerprint', 'user-id-name': 'pgp-name', 'user-id-email': 'email'};
    const pgpDetails = new Set(['uid', 'algorithm', 'key-length', 'creation-time', 'expiration-time', 'flags', 'keyserver', 'retrieval-url', 'signature-version', 'signature-type', 'public-key-algorithm', 'hash-algorithm', 'uid-sha256', 'user-attribute-sha256']);
    const objectDetails = {
        whois: new Set(['registrar', 'registrant-name', 'registrant-org', 'registrant-phone', 'creation-date', 'expiration-date', 'modification-date', 'text']),
        vulnerability: new Set(['summary', 'state', 'cvss-score', 'cvss-string', 'created', 'published', 'modified', 'credit', 'impact', 'references']),
        weakness: new Set(['status', 'weakness-abs']),
        annotation: new Set(['text', 'type', 'format', 'creation-date', 'modification-date', 'ref']),
        'epss-score': new Set(['score', 'percentile', 'date', 'reference']),
        'known-exploited-vulnerability': new Set(['exploited', 'status-reason', 'status-updated-at', 'first-seen-at', 'recorded-at', 'evidence-source', 'reference']),
        'vulnerability-sighting': new Set(['type', 'observed-at', 'content', 'reference']),
    };
    const separateDetails = new Set(['annotation', 'epss-score', 'known-exploited-vulnerability', 'vulnerability-sighting']);
    const canonical = value => JSON.stringify(value);

    function hash(value) {
        let a = 1779033703;
        let b = 3144134277;
        let c = 1013904242;
        let d = 2773480762;
        for (let i = 0; i < value.length; i++) {
            const code = value.charCodeAt(i);
            a = b ^ Math.imul(a ^ code, 597399067);
            b = c ^ Math.imul(b ^ code, 2869860233);
            c = d ^ Math.imul(c ^ code, 951274213);
            d = a ^ Math.imul(d ^ code, 2716044179);
        }
        a = Math.imul(c ^ (a >>> 18), 597399067);
        b = Math.imul(d ^ (b >>> 22), 2869860233);
        c = Math.imul(a ^ (c >>> 17), 951274213);
        d = Math.imul(b ^ (d >>> 19), 2716044179);
        return [a ^ b ^ c ^ d, b ^ a, c ^ a, d ^ a].map(part => (part >>> 0).toString(16).padStart(8, '0')).join('');
    }

    function identity(kind, value) {
        const key = canonical(value);
        return {id: 'misp:' + kind + ':' + hash(key), identity: key};
    }

    function humanize(value) {
        return ({ip: 'IP address', AS: 'Autonomous system', 'ssh-fingerprint': 'SSH fingerprint', url: 'URL', 'onion-address': 'Onion address'}[value]) || String(value).replace(/[_-]/g, ' ').replace(/^./, first => first.toUpperCase());
    }

    function shorten(value, length = 42) {
        value = String(value);
        return value.length > length ? value.slice(0, length - 12) + '…' + value.slice(-11) : value;
    }

    function normalizedObservable(type, value) {
        if (!scalar(value)) {
            throw new ConversionError('Invalid observable value.');
        }
        let family = ['ip', 'ip-src', 'ip-dst'].includes(type) ? 'ip' : ['domain', 'hostname'].includes(type) ? 'domain' : ['email', 'email-src', 'email-dst', 'whois-registrant-email'].includes(type) ? 'email' : type;
        value = String(value).trim();
        if (family === 'ip') {
            if (/^\d+\.\d+\.\d+\.\d+$/.test(value) && value.split('.').every(part => Number(part) <= 255)) {
                value = value.split('.').map(Number).join('.');
            } else if (value.includes(':')) {
                try {
                    value = new URL('http://[' + value.replace(/^\[|\]$/g, '') + ']/').hostname.slice(1, -1);
                } catch (error) {
                    throw new ConversionError('Invalid IP address.');
                }
            }
        } else if (family === 'domain' || family === 'onion-address') {
            value = value.toLowerCase().replace(/\.$/, '');
            if (value.endsWith('.onion')) {
                family = 'onion-address';
            }
        } else if (['md5', 'sha1', 'sha256', 'sha512', 'tlsh', 'x509-fingerprint-sha1', 'x509-fingerprint-sha256'].includes(family)) {
            value = value.toLowerCase();
        } else if (family === 'pgp-key-id' || family === 'pgp-fingerprint') {
            value = value.replace(/^0x/i, '').replace(/\s+/g, '').toUpperCase();
        } else if (family === 'weakness' || family === 'vulnerability' && /^(CVE-|GCVE-|GHSA-)/i.test(value)) {
            value = value.toUpperCase();
        } else if (family === 'url') {
            try {
                value = new URL(value).href;
            } catch (error) {
                // Keep provider URL values that cannot be parsed, without rewriting them.
            }
        } else if (family === 'AS') {
            value = value.replace(/^AS\s*/i, '');
        } else if (family === 'ssh-fingerprint' && /^(MD5:)?[a-f0-9:]+$/i.test(value)) {
            value = value.replace(/^MD5:/i, '').toLowerCase();
        }
        return {type: family, value, key: canonical([family, value])};
    }

    function pgpObservable(id) {
        const match = /^pgp:(key|name|mail):(.+)$/.exec(id);
        return match ? normalizedObservable({key: 'pgp-key-id', name: 'pgp-name', mail: 'email'}[match[1]], match[2]) : null;
    }

    function baseIndex(nodes) {
        const index = new Map();
        for (const node of nodes) {
            const metadata = dataOf(node)._misp;
            let observable;
            if (metadata?.kind === 'observable') {
                observable = normalizedObservable(metadata.type, metadata.value);
            } else if (!metadata) {
                observable = pgpObservable(node.id);
                const match = /^(domain|ip|ssh-key|decoded|cve)::(.+)$/.exec(node.id);
                if (match) {
                    observable = normalizedObservable({domain: 'domain', ip: 'ip', 'ssh-key': 'ssh-fingerprint', decoded: 'sha1', cve: 'vulnerability'}[match[1]], match[2]);
                }
            }
            if (observable) {
                const matches = index.get(observable.key) || new Set();
                matches.add(node.id);
                index.set(observable.key, matches);
            }
        }
        return index;
    }

    function validateAttribute(attribute) {
        if (!attribute || typeof attribute.type !== 'string' || !(scalar(attribute.value) || attribute.type === 'boolean' && typeof attribute.value === 'boolean')) {
            throw new ConversionError('Invalid MISP attribute.');
        }
    }

    function seenField(name) {
        const key = String(name).toLowerCase().replace(/_/g, '-');
        return ['first-seen', 'firstseen', 'time-first'].includes(key) ? 'First seen' : ['last-seen', 'lastseen', 'time-last'].includes(key) ? 'Last seen' : null;
    }

    function fieldsFor(record, attributes = []) {
        const grouped = new Map();
        const put = (name, value) => {
            if (!(scalar(value) || typeof value === 'boolean') || value === '') {
                return;
            }
            const values = grouped.get(name) || new Set();
            values.add(String(value));
            grouped.set(name, values);
        };
        put('First seen', record.first_seen);
        put('Last seen', record.last_seen);
        put('Comment', record.comment);
        for (const attribute of attributes) {
            const relation = attribute.object_relation || attribute.type;
            const key = relation.toLowerCase().replace(/_/g, '-');
            const date = seenField(key);
            if (date) {
                if (!grouped.has(date)) {
                    put(date, attribute.value);
                }
            } else if (metadataRelations.has(key) || observableTypes.has(attribute.type) || objectDetails[record.name]?.has(key) || pgpObjects.has(record.name) && (Object.hasOwn(pgpRelations, key) || pgpDetails.has(key))) {
                put(humanize(relation), attribute.value);
            }
        }
        for (const element of [record, ...attributes]) {
            for (const tag of element.Tag || []) {
                put('Tags', tag?.name);
            }
        }
        for (const galaxy of record.Galaxy || []) {
            put('Galaxy', galaxy?.name);
            for (const cluster of galaxy.GalaxyCluster || []) {
                put('Galaxy', cluster?.value);
            }
        }
        return [...grouped].map(([name, values]) => ({name, value: values.size === 1 ? [...values][0] : [...values]}));
    }

    function attributeObservable(attribute, object) {
        validateAttribute(attribute);
        if (seenField(attribute.object_relation || '') || attribute.type === 'datetime') {
            return null;
        }
        if (observableTypes.has(attribute.type)) {
            return normalizedObservable(attribute.type, attribute.value);
        }
        if (pgpObjects.has(object?.name) && Object.hasOwn(pgpRelations, attribute.object_relation)) {
            return normalizedObservable(pgpRelations[attribute.object_relation], attribute.value);
        }
        if (object?.name === 'passive-dns') {
            const relation = attribute.object_relation;
            const rrtype = object.Attribute.find(item => item.object_relation === 'rrtype')?.value;
            if (relation === 'rrname') {
                return normalizedObservable('domain', attribute.value);
            }
            if (relation === 'rdata' && ['A', 'AAAA'].includes(rrtype)) {
                return normalizedObservable('ip', attribute.value);
            }
            if (relation === 'rdata' && ['CNAME', 'PTR', 'NS'].includes(rrtype)) {
                return normalizedObservable('domain', attribute.value);
            }
        }
        return null;
    }

    function convertResponse(response, options = {}) {
        if (!response || !['success', 'empty'].includes(response.status)) {
            throw new ConversionError('A failed expansion cannot add graph results.');
        }
        const source = response.source?.global_id;
        if (![source, response.module, response.input?.id].every(value => typeof value === 'string' && value)) {
            throw new ConversionError('An expansion needs its AIL source, module, and input selector.');
        }
        validateAttribute(response.input);
        const baseNodes = options.baseNodes || [];
        const existing = new Map(baseNodes.map(node => [node.id, node]));
        if (!existing.has(source)) {
            throw new ConversionError('The original AIL node must be present in the graph.');
        }
        const sourceStyle = existing.get(source).getStyle?.() || existing.get(source).style || {};
        const sourceSize = Number(sourceStyle.size ?? sourceStyle.node_radius ?? sourceStyle.radius ?? 5);
        const nodeSize = Math.min(5, Number.isFinite(sourceSize) && sourceSize > 0 ? sourceSize : 5);
        const provenance = {module: response.module, source, executed_at: response.executed_at || null};
        const fragment = {source, nodes: [], edges: [], details: new Map()};
        if (response.status === 'empty') {
            return fragment;
        }
        const nodes = new Map();
        const edges = new Map();
        const aliases = new Map();
        const observables = baseIndex(baseNodes);
        const input = pgpObservable(source) || normalizedObservable(response.input.type, response.input.value);
        const inputAliases = new Set([response.source.object_uuid, response.source.input_object_uuid, response.source.attribute_uuid, response.input.uuid].filter(Boolean));
        const references = [];
        const returned = new Set();
        const link = (uuid, id) => {
            if (typeof uuid === 'string' && uuid) {
                const ids = aliases.get(uuid) || new Set();
                ids.add(id);
                aliases.set(uuid, ids);
            }
        };
        inputAliases.forEach(uuid => link(uuid, source));
        const describe = (id, context, fields) => {
            const summaries = fragment.details.get(id) || [];
            const summary = {context, fields, provenance};
            if (!summaries.some(entry => entry.context === context && canonical(entry.fields) === canonical(fields))) {
                summaries.push(summary);
            }
            fragment.details.set(id, summaries);
        };
        const addNode = (kind, parts, label, metadata) => {
            const identifiers = identity(kind, parts);
            const previous = nodes.get(identifiers.id) || existing.get(identifiers.id);
            const known = previous?.identity || dataOf(previous)._misp?.identity;
            if (known && known !== identifiers.identity) {
                throw new ConversionError('Graph identity collision.');
            }
            const descriptor = {...identifiers, data: {label, type: kind === 'observation' ? 'MISP observation' : humanize(metadata.type || 'Ambiguous observable'), origin: 'MISP Modules', _misp: {kind, can_expand: false, identity: identifiers.identity, ...metadata}}, style: {color: kind === 'observation' ? '#7c3aed' : ({ip: '#2563eb', domain: '#15803d', 'onion-address': '#15803d', 'ssh-fingerprint': '#b45309'}[metadata.type] || '#0d9488'), size: nodeSize, shape: kind === 'observation' ? 'square' : 'circle', text: ''}};
            if (!nodes.has(descriptor.id)) {
                nodes.set(descriptor.id, descriptor);
            }
            return descriptor.id;
        };
        const observableNode = (attribute, object) => {
            const observable = attributeObservable(attribute, object);
            if (!observable) {
                return null;
            }
            let id;
            if (inputAliases.has(attribute.uuid) || observable.key === input.key) {
                id = source;
            } else {
                const matches = observables.get(observable.key);
                id = matches?.size === 1 ? [...matches][0] : addNode('observable', [observable.type, observable.value], observable.type === 'AS' ? 'AS' + observable.value : observable.value, {type: observable.type, attribute_type: attribute.type, value: observable.value});
                observables.set(observable.key, new Set([id]));
            }
            link(attribute.uuid, id);
            returned.add(id);
            return {id, key: observable.key, role: attribute.object_relation || attribute.type};
        };
        const addEdge = (from, to, label) => {
            if (from === to) {
                return;
            }
            const identifiers = identity('edge', [from, to, label]);
            if (!edges.has(identifiers.id)) {
                edges.set(identifiers.id, {...identifiers, from, to, directed: true, data: {label, origin: 'MISP Modules', _misp: {kind: 'relationship', identity: identifiers.identity}}});
            }
        };

        if (response.format === 'legacy') {
            if (!Array.isArray(response.results)) {
                throw new ConversionError('Invalid legacy module results.');
            }
            for (const record of response.results) {
                if (!record || !Array.isArray(record.types) || !record.types.length || !record.types.every(type => typeof type === 'string') || !Array.isArray(record.values) || !record.values.every(scalar)) {
                    throw new ConversionError('Invalid legacy module record.');
                }
                const types = [...new Set(record.types)].sort();
                const families = new Set(types.map(type => normalizedObservable(type, '').type));
                const fields = fieldsFor(record);
                for (const value of record.values) {
                    let id;
                    if (families.size === 1) {
                        id = observableNode({type: types[0], value})?.id;
                    } else {
                        id = addNode('ambiguous', [types, String(value)], types.join(' / ') + ': ' + value, {types, value: String(value)});
                        returned.add(id);
                    }
                    if (id) {
                        describe(id, 'Lookup result', [...fields, {name: 'Returned types', value: types}]);
                    } else {
                        describe(source, 'Lookup result', [{name: humanize(types.join(' / ')), value: String(value)}]);
                    }
                }
            }
        } else if (response.format === 'misp_standard') {
            const results = response.results;
            if (!results || typeof results !== 'object' || Array.isArray(results) || ['Attribute', 'Object', 'ObjectReference'].some(key => results[key] !== undefined && !Array.isArray(results[key]))) {
                throw new ConversionError('Invalid structured module results.');
            }
            const context = fieldsFor(results);
            if (context.length) {
                describe(source, 'Expansion context', context);
            }
            for (const object of results.Object || []) {
                if (!object || typeof object.name !== 'string' || !object.name || typeof object.uuid !== 'string' || !object.uuid || !Array.isArray(object.Attribute)) {
                    throw new ConversionError('Invalid returned MISP object.');
                }
                const members = object.Attribute.map(attribute => observableNode(attribute, object)).filter(Boolean);
                const fields = fieldsFor(object, object.Attribute);
                const hasOtherObservable = members.some(member => member.id !== source);
                const identifier = ['vulnerability', 'weakness'].includes(object.name) ? members.find(member => member.role === 'id') : null;
                const needsObservation = hasOtherObservable || separateDetails.has(object.name) && fields.length;
                const observation = identifier?.id || (needsObservation && !inputAliases.has(object.uuid) ? addNode('observation', [object.name, [...new Set(members.map(member => member.key))].sort(), source, ...(separateDetails.has(object.name) ? [fields] : [])], object.name, {object_name: object.name}) : source);
                link(object.uuid, observation);
                describe(observation, object.name, fields);
                if (observation !== source) {
                    returned.add(observation);
                }
                if (observation !== source || identifier) {
                    for (const member of members) {
                        addEdge(observation, member.id, member.role);
                        describe(member.id, object.name, fields.filter(field => ['First seen', 'Last seen', 'Tags'].includes(field.name)));
                    }
                }
                if (!Array.isArray(object.ObjectReference || [])) {
                    throw new ConversionError('Invalid returned MISP references.');
                }
                references.push(...(object.ObjectReference || []).map(reference => ({from: observation, reference})));
            }
            for (const attribute of results.Attribute || []) {
                const member = observableNode(attribute);
                describe(member?.id || source, 'Attribute', fieldsFor(attribute, [attribute]));
            }
            references.push(...(results.ObjectReference || []).map(reference => ({reference})));
            for (const pending of references) {
                const record = pending.reference;
                if (!record || typeof record.referenced_uuid !== 'string' || !record.referenced_uuid || typeof record.relationship_type !== 'string' || !record.relationship_type) {
                    throw new ConversionError('Invalid returned MISP reference.');
                }
                const from = pending.from ? new Set([pending.from]) : aliases.get(record.object_uuid);
                const to = aliases.get(record.referenced_uuid);
                if (from?.size === 1 && to?.size === 1) {
                    addEdge([...from][0], [...to][0], record.relationship_type);
                } else {
                    describe(pending.from || source, 'Unresolved relationship', [{name: 'Relationship', value: record.relationship_type}, {name: 'Reason', value: from?.size > 1 || to?.size > 1 ? 'Ambiguous reference' : 'Missing referenced entity'}]);
                }
            }
        } else {
            throw new ConversionError('Unsupported module result format.');
        }

        // Connect each returned component to the actual query origin. A match to a
        // different AIL node does not alone establish a link to that origin.
        const adjacency = new Map([...returned].map(id => [id, new Set()]));
        adjacency.set(source, new Set());
        for (const edge of edges.values()) {
            if (!adjacency.has(edge.from)) {
                adjacency.set(edge.from, new Set());
            }
            if (!adjacency.has(edge.to)) {
                adjacency.set(edge.to, new Set());
            }
            adjacency.get(edge.from).add(edge.to);
            adjacency.get(edge.to).add(edge.from);
        }
        const visited = new Set();
        for (const id of [source, ...returned]) {
            if (visited.has(id)) {
                continue;
            }
            const queue = [id];
            const component = [];
            while (queue.length) {
                const current = queue.pop();
                if (visited.has(current)) {
                    continue;
                }
                visited.add(current);
                component.push(current);
                queue.push(...(adjacency.get(current) || []));
            }
            if (!component.includes(source) && component.length) {
                const anchor = component.find(id => dataOf(nodes.get(id) || existing.get(id))._misp?.kind === 'observation') || component[0];
                addEdge(anchor, source, 'expanded-from');
            }
        }
        fragment.nodes = [...nodes.values()];
        fragment.edges = [...edges.values()];
        for (const edge of fragment.edges) {
            const summaries = fragment.details.get(edge.from) || fragment.details.get(edge.to) || [{context: 'Relationship', fields: [], provenance}];
            fragment.details.set(edge.id, summaries);
        }
        return fragment;
    }

    function isExpansionNode(node) {
        return Boolean(dataOf(node)._misp);
    }

    return {ConversionError, convertResponse, normalizedObservable, fieldsFor, humanize, shorten, isExpansionNode};
});
