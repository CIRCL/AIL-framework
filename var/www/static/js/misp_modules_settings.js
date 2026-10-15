'use strict';

document.addEventListener('DOMContentLoaded', () => {
    const root = document.getElementById('misp-module-settings');
    if (!root) {
        return;
    }
    let state = JSON.parse(document.getElementById('misp-settings-data').textContent);
    let selected = null;
    let filter = 'all';
    let serviceDirty = false;
    let busy = false;
    const drafts = new Map();
    const grid = document.getElementById('misp-module-grid');
    const panels = document.getElementById('misp-module-panels');
    const refreshButton = document.getElementById('misp-refresh');
    const serviceForm = document.getElementById('misp-service-form');
    const search = document.getElementById('misp-module-search');

    function element(tag, className, text) {
        const node = document.createElement(tag);
        node.className = className || '';
        if (text !== undefined) {
            node.textContent = text;
        }
        return node;
    }

    function maskSecret(value) {
        const characters = Array.from(String(value));
        if (characters.length <= 4) {
            return '*'.repeat(characters.length);
        }
        return characters.slice(0, 2).join('') + '*'.repeat(characters.length - 4) + characters.slice(-2).join('');
    }

    function message(text, kind = 'success') {
        const box = document.getElementById('misp-message');
        box.className = 'alert alert-' + kind;
        box.textContent = text;
    }

    async function request(url, payload) {
        const options = {credentials: 'same-origin', cache: 'no-store', headers: {'Accept': 'application/json'}};
        if (payload !== undefined) {
            options.method = 'POST';
            options.headers['Content-Type'] = 'application/json';
            options.headers['X-CSRF-Token'] = root.dataset.csrfToken;
            options.body = JSON.stringify(payload);
        }
        const response = await fetch(url, options);
        let data;
        try {
            data = await response.json();
        } catch (error) {
            throw new Error('Unable to read the response. Reload this page and check that you are still logged in.');
        }
        if (!response.ok || data.status === 'error') {
            throw new Error(data.reason || 'Unable to update MISP Module settings.');
        }
        return data;
    }

    function setBusy(value) {
        busy = value;
        refreshButton.disabled = value;
        document.querySelectorAll('[data-module-toggle], [data-module-save], #misp-service-save').forEach(node => {
            node.disabled = value;
        });
        root.setAttribute('aria-busy', String(value));
    }

    function renderService() {
        if (!serviceDirty) {
            document.getElementById('misp-service-enabled').checked = state.service.enabled;
            ['url', 'port', 'timeout'].forEach(key => {
                document.getElementById('misp-service-' + key).value = state.service[key];
            });
        }
        const badge = document.getElementById('misp-service-status');
        const health = state.service.health;
        badge.className = 'badge mr-3 badge-' + (health === 'available' ? 'success' : health === 'unavailable' ? 'danger' : 'secondary');
        badge.textContent = health === 'available' ? 'Connected' : health === 'unavailable' ? 'Unavailable' : 'Not checked';
        const warning = document.getElementById('misp-service-error');
        warning.classList.toggle('d-none', !state.service.error);
        warning.textContent = state.service.error ? state.service.error.reason + ' You can still edit and save module settings.' : '';
        document.getElementById('misp-service-note').textContent = state.service.enabled ? 'Changes apply to new expansion requests.' : 'Graph expansion is disabled. You can configure modules before enabling it.';
    }

    function moduleStatus(module) {
        if (module.missing_configuration.length) {
            return ['Needs configuration', 'warning'];
        }
        if (module.configuration_status === 'unsupported_format') {
            return ['Unsupported format', 'danger'];
        }
        if (module.discovered === false) {
            return ['Not on service', 'secondary'];
        }
        if (module.enabled && state.service.health === 'unavailable') {
            return ['Service unavailable', 'secondary'];
        }
        return module.enabled ? ['Enabled', 'success'] : ['Disabled', 'secondary'];
    }

    function showSelected(name) {
        selected = name;
        grid.querySelectorAll('[data-module-card]').forEach(card => {
            const active = card.dataset.moduleCard === selected;
            card.classList.toggle('selected', active);
            card.querySelector('[data-module-open]').setAttribute('aria-expanded', String(active));
        });
        panels.querySelectorAll('[data-module-panel]').forEach(panel => {
            panel.classList.toggle('d-none', panel.dataset.modulePanel !== selected);
        });
    }

    function applyFilters() {
        const query = search.value.trim().toLowerCase();
        let visible = 0;
        const counts = {all: state.modules.length, enabled: 0, config: 0};
        state.modules.forEach(module => {
            counts.enabled += Number(module.enabled);
            counts.config += Number(module.missing_configuration.length > 0);
            const matchesSearch = [module.name, module.label, module.description].join(' ').toLowerCase().includes(query);
            const matchesFilter = filter === 'all' || (filter === 'enabled' && module.enabled) || (filter === 'config' && module.missing_configuration.length > 0);
            const card = grid.querySelector('[data-module-card="' + module.name + '"]');
            card.classList.toggle('d-none', !matchesSearch || !matchesFilter);
            visible += Number(matchesSearch && matchesFilter);
        });
        document.querySelectorAll('[data-count]').forEach(node => {
            node.textContent = counts[node.dataset.count];
        });
        document.getElementById('misp-module-empty').classList.toggle('d-none', visible !== 0);
    }

    function renderCards() {
        grid.replaceChildren();
        state.modules.forEach(module => {
            const card = element('article', 'misp-module-card' + (module.enabled ? '' : ' off'));
            card.dataset.moduleCard = module.name;
            const header = element('div', 'd-flex align-items-start justify-content-between');
            const name = element('button', 'btn btn-link p-0 misp-module-name mr-2', module.label);
            name.type = 'button';
            name.dataset.moduleOpen = module.name;
            name.setAttribute('aria-controls', 'misp-panel-' + module.name);
            name.addEventListener('click', () => showSelected(module.name));
            const switchLabel = element('label', 'misp-switch mb-0');
            const toggle = element('input');
            toggle.type = 'checkbox';
            toggle.checked = module.enabled;
            toggle.dataset.moduleToggle = module.name;
            toggle.setAttribute('role', 'switch');
            toggle.setAttribute('aria-label', 'Enable ' + module.name);
            toggle.addEventListener('change', () => saveModule(module, {enabled: toggle.checked}));
            switchLabel.append(toggle, element('span', 'misp-switch-track'));
            header.append(name, switchLabel);
            const footer = element('div', 'd-flex justify-content-between align-items-center');
            const [status, color] = moduleStatus(module);
            footer.append(element('span', 'badge badge-' + color, status));
            const configure = element('button', 'btn btn-link btn-sm p-0 ml-2', 'Configure');
            configure.type = 'button';
            configure.setAttribute('aria-label', 'Configure ' + module.name);
            configure.addEventListener('click', () => showSelected(module.name));
            footer.append(configure);
            card.append(header, element('p', 'misp-module-description', module.description), footer);
            grid.append(card);
        });
        showSelected(selected);
        applyFilters();
    }

    function renderField(module, field) {
        const group = element('div', 'form-group');
        const identifier = 'misp-field-' + module.name + '-' + field.name;
        const label = element('label', '', field.name + (field.required ? ' (required)' : ''));
        label.htmlFor = identifier;
        let input;
        if (field.type === 'boolean' || field.type === 'bool') {
            input = element('select', 'form-control');
            [['', 'Not set'], ['true', 'Yes'], ['false', 'No']].forEach(([value, text]) => {
                const option = element('option', '', text);
                option.value = value;
                input.append(option);
            });
        } else {
            input = element('input', 'form-control');
            input.type = field.secret ? 'password' : ['integer', 'int', 'number', 'float'].includes(field.type) ? 'number' : 'text';
            if (input.type === 'number') {
                input.step = ['integer', 'int'].includes(field.type) ? '1' : 'any';
            }
        }
        input.id = identifier;
        input.autocomplete = field.secret ? 'new-password' : 'off';
        input.dataset.configField = field.name;
        const draft = drafts.get(module.name) || {};
        const changed = Object.hasOwn(draft, field.name);
        input.value = changed ? (draft[field.name] ?? '') : field.secret ? '' : (field.value ?? '');
        input.placeholder = field.secret && field.configured ? 'Enter a replacement' : '';
        const help = element('small', 'form-text text-muted');
        help.id = identifier + '-help';
        if (field.secret && field.configured) {
            const saved = element('span', 'd-block');
            const preview = element('code', 'misp-secret-preview', field.masked_value);
            preview.dataset.configPreview = field.name;
            saved.append(document.createTextNode('Saved value: '), preview);
            help.append(saved, document.createTextNode('Leave blank to keep the saved value, or enter a replacement.'));
        } else {
            help.textContent = field.secret ? 'No value is saved.' : field.description || '';
        }
        input.setAttribute('aria-describedby', help.id);
        const clear = element('input');
        clear.type = 'checkbox';
        clear.checked = changed && draft[field.name] === null;
        clear.setAttribute('aria-label', 'Clear saved ' + field.name);
        input.disabled = clear.checked;
        function remember() {
            const values = drafts.get(module.name) || {};
            if (clear.checked) {
                values[field.name] = null;
            } else if (field.secret && input.value === '') {
                delete values[field.name];
            } else {
                values[field.name] = input.value;
            }
            drafts.set(module.name, values);
        }
        input.addEventListener('input', remember);
        input.addEventListener('change', remember);
        group.append(label, input, help);
        if (field.secret && field.configured) {
            const clearLabel = element('label', 'd-flex align-items-center small text-muted mt-2');
            clear.className = 'mr-2';
            clear.addEventListener('change', () => {
                input.disabled = clear.checked;
                remember();
            });
            clearLabel.append(clear, document.createTextNode('Clear saved value'));
            group.append(clearLabel);
        }
        return group;
    }

    function renderPanels() {
        panels.replaceChildren();
        state.modules.forEach(module => {
            const panel = element('div', 'card shadow-sm');
            panel.id = 'misp-panel-' + module.name;
            panel.dataset.modulePanel = module.name;
            const header = element('div', 'card-header bg-white');
            header.append(element('div', 'small text-muted', 'Module settings'), element('h5', 'mb-0 misp-panel-heading', module.name));
            const body = element('div', 'card-body');
            body.append(element('p', 'text-muted small', module.description));
            if (module.metadata_source === 'builtin') {
                body.append(element('p', 'small text-muted', 'Showing known configuration fields. Check the connection to load fields from the service.'));
            }
            const form = element('form');
            form.dataset.moduleForm = module.name;
            module.fields.forEach(field => form.append(renderField(module, field)));
            if (!module.fields.length) {
                form.append(element('p', 'text-muted', 'This module needs no additional configuration.'));
            } else {
                const save = element('button', 'btn btn-primary', 'Save module');
                save.type = 'submit';
                save.dataset.moduleSave = module.name;
                form.append(save);
            }
            form.addEventListener('submit', event => {
                event.preventDefault();
                const config = drafts.get(module.name) || {};
                if (!Object.keys(config).length) {
                    message('No module settings have changed.', 'info');
                    return;
                }
                saveModule(module, {config});
            });
            body.append(form);
            panel.append(header, body);
            panels.append(panel);
        });
        showSelected(selected);
    }

    async function saveModule(module, payload) {
        if (busy) {
            return;
        }
        setBusy(true);
        const form = panels.querySelector('[data-module-form="' + module.name + '"]');
        form.querySelectorAll('input, select').forEach(node => {
            node.disabled = true;
        });
        try {
            await request(root.dataset.moduleUrl.replace('MODULE_NAME', encodeURIComponent(module.name)), payload);
            if (payload.enabled !== undefined) {
                module.enabled = payload.enabled;
            }
            if (payload.config) {
                module.fields.forEach(field => {
                    if (Object.hasOwn(payload.config, field.name)) {
                        const value = payload.config[field.name];
                        field.configured = value !== null && String(value).trim() !== '';
                        field.value = field.secret ? null : value;
                        field.masked_value = field.secret && field.configured ? maskSecret(value) : null;
                    }
                });
                drafts.delete(module.name);
            }
            const names = module.fields.map(field => field.name);
            module.missing_configuration = module.missing_configuration.filter(name => !names.includes(name)).concat(module.fields.filter(field => field.required && !field.configured).map(field => field.name));
            renderCards();
            renderPanels();
            message(module.name + ' settings saved.');
        } catch (error) {
            renderCards();
            renderPanels();
            message(error.message, 'danger');
        } finally {
            setBusy(false);
        }
    }

    async function refresh() {
        if (busy) {
            return;
        }
        setBusy(true);
        refreshButton.textContent = 'Checking…';
        try {
            state = await request(root.dataset.settingsUrl + '?check_connection=true');
            renderService();
            renderCards();
            renderPanels();
        } catch (error) {
            message(error.message, 'danger');
        } finally {
            refreshButton.textContent = 'Check connection';
            setBusy(false);
        }
    }

    serviceForm.addEventListener('input', () => {
        serviceDirty = true;
    });
    serviceForm.addEventListener('submit', async event => {
        event.preventDefault();
        if (busy) {
            return;
        }
        setBusy(true);
        const payload = {enabled: document.getElementById('misp-service-enabled').checked, url: document.getElementById('misp-service-url').value, port: document.getElementById('misp-service-port').value, timeout: document.getElementById('misp-service-timeout').value};
        serviceForm.querySelectorAll('input').forEach(node => {
            node.disabled = true;
        });
        try {
            const saved = await request(root.dataset.serviceUrl, payload);
            state.service = saved.service;
            serviceDirty = false;
            renderService();
            renderCards();
            message('Service settings saved.');
        } catch (error) {
            message(error.message, 'danger');
        } finally {
            serviceForm.querySelectorAll('input').forEach(node => {
                node.disabled = false;
            });
            setBusy(false);
        }
    });
    refreshButton.addEventListener('click', refresh);
    search.addEventListener('input', applyFilters);
    document.querySelectorAll('[data-filter]').forEach(button => {
        button.addEventListener('click', () => {
            filter = button.dataset.filter;
            document.querySelectorAll('[data-filter]').forEach(chip => {
                const active = chip === button;
                chip.classList.toggle('active', active);
                chip.setAttribute('aria-pressed', String(active));
            });
            applyFilters();
        });
    });
    window.toggle_sidebar = () => {
        const menu = document.getElementById('nav_menu');
        const hidden = menu.classList.toggle('d-none');
        document.getElementById('side_menu').classList.toggle('col-lg-2', !hidden);
        document.getElementById('side_menu').classList.toggle('border-right', !hidden);
        document.getElementById('core_content').classList.toggle('col-lg-10', !hidden);
    };
    ['page-options', 'nav_misp_modules'].forEach(identifier => {
        document.getElementById(identifier)?.classList.add('active');
    });
    selected = state.modules.find(module => module.missing_configuration.length)?.name || state.modules.find(module => module.enabled)?.name || state.modules[0]?.name;
    renderService();
    renderCards();
    renderPanels();
    refresh();
});
