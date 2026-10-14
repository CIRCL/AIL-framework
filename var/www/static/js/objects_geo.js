(function () {
    'use strict';

    const PAGE_SIZE = 100;
    const MAP_MAX_LATITUDE = 85.05112878;
    let leafletAssets;

    function loadLeaflet(panel) {
        if (!leafletAssets) {
            leafletAssets = Promise.all([
                new Promise(function (resolve, reject) {
                    const css = document.createElement('link');
                    css.rel = 'stylesheet';
                    css.href = panel.dataset.leafletCss;
                    css.onload = resolve;
                    css.onerror = function () {
                        reject(new Error('Map styles could not be loaded.'));
                    };
                    document.head.appendChild(css);
                }),
                new Promise(function (resolve, reject) {
                    if (window.L) {
                        resolve();
                        return;
                    }
                    const script = document.createElement('script');
                    script.src = panel.dataset.leafletJs;
                    script.onload = resolve;
                    script.onerror = function () {
                        reject(new Error('Map library could not be loaded.'));
                    };
                    document.head.appendChild(script);
                })
            ]);
        }
        return leafletAssets;
    }

    class ObjectGeoPanel {
        constructor(panel) {
            this.panel = panel;
            this.canWrite = panel.dataset.canWrite === 'true';
            this.offset = 0;
            this.locations = [];
            this.total = 0;
            this.hasMore = false;
            this.loaded = false;
            this.busy = false;
            this.started = false;
            this.editing = null;
            this.conflicted = false;
            this.markers = new Map();
            this.table = panel.querySelector('tbody');
            this.form = panel.querySelector('.geo-form');
            this.status = panel.querySelector('.geo-status');
            this.mapStatus = panel.querySelector('.geo-map-status');
            panel.addEventListener('toggle', () => this.open());
            panel.querySelector('.geo-refresh').addEventListener('click', () => this.load(this.offset));
            panel.querySelector('.geo-prev').addEventListener('click', () => this.load(Math.max(0, this.offset - PAGE_SIZE)));
            panel.querySelector('.geo-next').addEventListener('click', () => this.load(this.offset + PAGE_SIZE));
            if (this.form) {
                this.latitude = panel.querySelector('.geo-latitude');
                this.longitude = panel.querySelector('.geo-longitude');
                this.form.addEventListener('submit', (event) => this.save(event));
                panel.querySelector('.geo-cancel').addEventListener('click', () => this.resetForm());
                this.form.addEventListener('input', () => this.previewCoordinates());
            }
            this.setBusy(false);
            this.open();
        }

        showStatus(message, error = false) {
            this.status.textContent = message;
            this.status.hidden = !message;
            this.status.classList.toggle('alert-danger', error);
            this.status.classList.toggle('alert-info', !error);
        }

        setBusy(busy) {
            this.busy = busy;
            this.panel.setAttribute('aria-busy', String(busy));
            this.panel.querySelectorAll('button, input').forEach((element) => {
                element.disabled = busy;
            });
            this.panel.querySelector('.geo-prev').disabled = busy || !this.loaded || this.offset === 0;
            this.panel.querySelector('.geo-next').disabled = busy || !this.loaded || !this.hasMore;
            this.panel.querySelectorAll('.geo-location-action').forEach((button) => {
                button.disabled = busy || !this.loaded;
            });
            if (this.form) {
                this.panel.querySelector('.geo-save').disabled = busy || !this.loaded || this.conflicted;
            }
        }

        async open() {
            if (!this.panel.open) {
                return;
            }
            if (!this.started) {
                this.started = true;
                this.load(0);
                try {
                    await loadLeaflet(this.panel);
                    this.initMap();
                } catch (error) {
                    this.panel.querySelector('.geo-map').hidden = true;
                    this.mapStatus.textContent = error.message + ' The coordinate table and manual entry remain available.';
                }
            }
            if (this.map) {
                this.map.invalidateSize();
            }
        }

        async jsonResponse(response) {
            let data;
            try {
                data = await response.json();
            } catch (error) {
                let reason;
                if (response.redirected || response.status === 401) {
                    reason = 'The location request requires authentication. Sign in and refresh the page.';
                } else if (response.status === 403) {
                    reason = 'Access to object locations was denied (HTTP 403).';
                } else if (response.status >= 500) {
                    reason = `The location server returned an error (HTTP ${response.status}). Check the AIL server logs and GEO database configuration.`;
                } else {
                    reason = `The location endpoint returned an unexpected response (HTTP ${response.status}). Check the server and proxy routes.`;
                }
                const responseError = new Error(reason);
                responseError.status = response.status;
                throw responseError;
            }
            if (!response.ok) {
                const error = new Error(data.reason || 'The location request failed.');
                error.status = response.status;
                throw error;
            }
            return data;
        }

        async request(method, geoId, payload, offset) {
            const url = new URL(this.panel.dataset.listUrl, window.location.origin);
            if (geoId) {
                url.pathname += '/' + encodeURIComponent(geoId);
            }
            url.searchParams.set('gid', this.panel.dataset.gid);
            const options = {method: method, credentials: 'same-origin', cache: 'no-store', headers: {Accept: 'application/json'}};
            if (method === 'GET') {
                url.searchParams.set('offset', offset);
                url.searchParams.set('limit', PAGE_SIZE);
            } else {
                const csrfResponse = await fetch(this.panel.dataset.csrfUrl, {credentials: 'same-origin', cache: 'no-store'});
                const csrf = await this.jsonResponse(csrfResponse);
                options.headers['X-CSRF-Token'] = csrf.csrf_token;
                options.headers['Content-Type'] = 'application/json';
                options.body = JSON.stringify(payload);
            }
            return this.jsonResponse(await fetch(url, options));
        }

        async load(offset, afterMutation = false) {
            if (this.busy && !afterMutation) {
                return;
            }
            this.setBusy(true);
            if (!afterMutation) {
                this.showStatus('Loading locations…');
            }
            try {
                let data = await this.request('GET', null, null, offset);
                if (offset > 0 && offset >= data.total) {
                    offset = Math.max(0, Math.floor((data.total - 1) / PAGE_SIZE) * PAGE_SIZE);
                    data = await this.request('GET', null, null, offset);
                }
                this.offset = offset;
                this.locations = data.locations;
                this.total = data.total;
                this.hasMore = data.has_more;
                this.loaded = true;
                this.render();
                if (!afterMutation) {
                    this.showStatus('');
                }
            } catch (error) {
                this.loaded = false;
                this.showStatus((afterMutation ? 'The change was saved, but locations could not be refreshed. ' : '') + error.message, true);
            } finally {
                this.setBusy(false);
            }
        }

        button(label, action) {
            const button = document.createElement('button');
            button.type = 'button';
            button.className = 'geo-location-action btn btn-sm btn-outline-secondary mr-1 mb-1';
            button.textContent = label;
            button.addEventListener('click', action);
            return button;
        }

        render() {
            this.table.replaceChildren();
            this.locations.forEach((location) => {
                const row = document.createElement('tr');
                row.dataset.geoId = location.geo_id;
                const updated = new Date(location.updated_at).toLocaleString();
                [location.latitude, location.longitude, location.source || '—', updated].forEach((value) => {
                    const cell = document.createElement('td');
                    cell.textContent = String(value);
                    row.appendChild(cell);
                });
                const actions = document.createElement('td');
                actions.appendChild(this.button('View on map', () => this.focus(location)));
                if (this.canWrite) {
                    actions.appendChild(this.button('Edit', () => this.edit(location)));
                    actions.appendChild(this.button('Remove', () => this.remove(location)));
                }
                row.appendChild(actions);
                this.table.appendChild(row);
            });
            const count = this.panel.querySelector('.geo-count');
            count.textContent = this.total;
            count.hidden = false;
            count.removeAttribute('title');
            count.removeAttribute('aria-label');
            this.panel.querySelector('.geo-empty').hidden = this.total !== 0;
            this.panel.querySelector('.geo-page').textContent = this.total ? `${this.offset + 1}–${this.offset + this.locations.length} of ${this.total} locations` : '0 locations';
            this.drawMarkers();
            this.highlight();
        }

        initMap() {
            this.map = L.map(this.panel.querySelector('.geo-map'), {worldCopyJump: true, attributionControl: false}).setView([20, 0], 2);
            this.layer = L.layerGroup().addTo(this.map);
            this.map.on('moveend', () => {
                this.markers.forEach((marker) => {
                    if (marker.isTooltipOpen()) {
                        this.keepTooltipInMap(marker.getTooltip());
                    }
                });
            });
            const tiles = L.tileLayer('https://geo.circl.lu/hot/{z}/{x}/{y}.png', {maxZoom: 19}).addTo(this.map);
            tiles.on('tileerror', () => {
                this.tilesUnavailable = true;
                this.updateMapStatus();
            });
            if (this.canWrite) {
                this.map.on('click', (event) => {
                    if (this.busy) {
                        return;
                    }
                    this.latitude.value = Math.max(-90, Math.min(90, event.latlng.lat)).toFixed(6);
                    this.longitude.value = event.latlng.wrap().lng.toFixed(6);
                    this.previewCoordinates();
                });
            }
            this.drawMarkers();
            this.previewCoordinates();
        }

        mapPosition(location) {
            const longitude = location.longitude;
            const anchor = this.locations.length ? this.locations[0].longitude : longitude;
            const wrapped = anchor + ((longitude - anchor + 540) % 360) - 180;
            return [Math.max(-MAP_MAX_LATITUDE, Math.min(MAP_MAX_LATITUDE, location.latitude)), wrapped];
        }

        locationDetails(location) {
            const details = document.createElement('dl');
            details.className = 'geo-point-details';
            const fields = [
                ['Latitude', location.latitude],
                ['Longitude', location.longitude],
                ['Source', location.source],
                ['Created', new Date(location.created_at).toLocaleString()],
                ['Created by', location.created_by],
                ['Updated', new Date(location.updated_at).toLocaleString()],
                ['Updated by', location.updated_by],
                ['Revision', location.revision],
                ['Location ID', location.geo_id],
                ['Object', location.obj_gid]
            ];
            fields.forEach(([label, value]) => {
                if (value === undefined || value === null || value === '') {
                    return;
                }
                const term = document.createElement('dt');
                term.textContent = label;
                const description = document.createElement('dd');
                description.textContent = String(value);
                details.append(term, description);
            });
            return details;
        }

        keepTooltipInMap(tooltip) {
            const position = this.map.latLngToContainerPoint(tooltip.getLatLng());
            tooltip.options.direction = position.x < this.map.getSize().x / 2 ? 'right' : 'left';
            tooltip.options.offset = L.point(0, 0);
            tooltip.update();
            const bounds = tooltip.getElement().getBoundingClientRect();
            const mapBounds = this.map.getContainer().getBoundingClientRect();
            const left = Math.max(mapBounds.left + 8, Math.min(bounds.left, mapBounds.right - bounds.width - 8));
            const top = Math.max(mapBounds.top + 8, Math.min(bounds.top, mapBounds.bottom - bounds.height - 8));
            tooltip.options.offset = L.point(left - bounds.left, top - bounds.top);
            tooltip.update();
        }

        drawMarkers() {
            if (!this.map) {
                return;
            }
            this.layer.clearLayers();
            this.markers.clear();
            const positions = [];
            this.locations.forEach((location) => {
                const position = this.mapPosition(location);
                positions.push(position);
                const popup = document.createElement('div');
                popup.appendChild(this.locationDetails(location));
                if (this.canWrite) {
                    popup.appendChild(this.button('Edit this location', () => this.edit(location)));
                }
                const marker = L.circleMarker(position, {radius: 7, color: '#1769aa', fillOpacity: 0.8}).addTo(this.layer);
                marker.bindTooltip(this.locationDetails(location), {className: 'geo-point-tooltip', opacity: 1});
                marker.on('tooltipopen', (event) => this.keepTooltipInMap(event.tooltip));
                marker.bindPopup(popup, {maxWidth: 380});
                this.markers.set(location.geo_id, marker);
            });
            this.map.invalidateSize();
            if (positions.length) {
                this.map.fitBounds(L.latLngBounds(positions), {padding: [30, 30], maxZoom: 13});
            }
            this.updateMapStatus();
        }

        updateMapStatus() {
            const polar = this.locations.some((location) => Math.abs(location.latitude) > MAP_MAX_LATITUDE);
            this.mapStatus.textContent = 'The map shows the current page of coordinates.'
                + (polar ? ' Polar points are drawn at the map latitude limit; the table retains the original coordinates.' : '')
                + (this.tilesUnavailable ? ' Map tiles are unavailable. Points and the coordinate table remain usable.' : '');
        }

        focus(location) {
            if (!this.map) {
                this.showStatus('The map is unavailable. Original coordinates are listed in the table.');
                return;
            }
            this.map.setView(this.mapPosition(location), 13);
            const marker = this.markers.get(location.geo_id);
            if (marker) {
                marker.openPopup();
            }
        }

        highlight() {
            this.table.querySelectorAll('tr').forEach((row) => {
                row.classList.toggle('geo-selected', Boolean(this.editing && row.dataset.geoId === this.editing.geo_id));
            });
        }

        edit(location) {
            if (this.busy || !this.loaded) {
                return;
            }
            this.editing = location;
            this.conflicted = false;
            this.latitude.value = location.latitude;
            this.longitude.value = location.longitude;
            this.panel.querySelector('.geo-form-title').textContent = 'Edit location';
            this.panel.querySelector('.geo-save').textContent = 'Save location';
            this.panel.querySelector('.geo-cancel').hidden = false;
            this.showStatus('Editing the selected location.');
            this.highlight();
            this.setBusy(false);
            this.focus(location);
            this.previewCoordinates();
            this.latitude.focus();
        }

        resetForm() {
            if (!this.form) {
                return;
            }
            this.editing = null;
            this.conflicted = false;
            this.form.reset();
            this.panel.querySelector('.geo-form-title').textContent = 'Add a location';
            this.panel.querySelector('.geo-save').textContent = 'Add location';
            this.panel.querySelector('.geo-cancel').hidden = true;
            this.highlight();
            this.previewCoordinates();
            this.setBusy(this.busy);
        }

        previewCoordinates() {
            if (!this.map || !this.form) {
                return;
            }
            if (this.preview) {
                this.preview.remove();
                this.preview = null;
            }
            if (this.latitude.value === '' || this.longitude.value === '' || !this.latitude.validity.valid || !this.longitude.validity.valid) {
                return;
            }
            const location = {latitude: Number(this.latitude.value), longitude: Number(this.longitude.value)};
            this.preview = L.circleMarker(this.mapPosition(location), {radius: 9, color: '#b45309', fillOpacity: 0.3, dashArray: '4 4'}).addTo(this.map);
        }

        async save(event) {
            event.preventDefault();
            if (this.busy || !this.loaded || this.conflicted || !this.form.reportValidity()) {
                return;
            }
            const payload = {latitude: Number(this.latitude.value), longitude: Number(this.longitude.value)};
            if (this.editing) {
                payload.expected_revision = this.editing.revision;
            }
            this.setBusy(true);
            try {
                const offset = this.editing ? this.offset : Math.floor(this.total / PAGE_SIZE) * PAGE_SIZE;
                await this.request(this.editing ? 'PATCH' : 'POST', this.editing && this.editing.geo_id, payload);
                this.resetForm();
                this.showStatus('Location saved.');
                await this.load(offset, true);
            } catch (error) {
                if (error.status === 409) {
                    this.conflicted = true;
                    await this.load(this.offset, true);
                    this.showStatus('This location changed. Your entered coordinates are preserved. Select Edit on the refreshed row before applying your changes.', true);
                } else {
                    this.showStatus(error.message, true);
                }
            } finally {
                this.setBusy(false);
            }
        }

        async remove(location) {
            if (this.busy || !this.loaded || !window.confirm(`Remove location at ${location.latitude}, ${location.longitude}?`)) {
                return;
            }
            this.setBusy(true);
            try {
                await this.request('DELETE', location.geo_id, {expected_revision: location.revision});
                if (this.editing && this.editing.geo_id === location.geo_id) {
                    this.resetForm();
                }
                this.showStatus('Location removed.');
                await this.load(this.offset, true);
            } catch (error) {
                if (error.status === 409) {
                    await this.load(this.offset, true);
                    this.showStatus('This location changed. Review the refreshed coordinates before removing it.', true);
                } else {
                    this.showStatus(error.message, true);
                }
            } finally {
                this.setBusy(false);
            }
        }
    }

    document.querySelectorAll('.object-geo').forEach(function (panel) {
        new ObjectGeoPanel(panel);
    });
}());
