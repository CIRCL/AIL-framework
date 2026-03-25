(function () {
    function escapeYaraString(value) {
        return value
            .replace(/\\/g, '\\\\')
            .replace(/"/g, '\\"')
            .replace(/\r/g, '\\r')
            .replace(/\n/g, '\\n')
            .replace(/\t/g, '\\t');
    }

    function createStringRow(index) {
        return `
            <div class="border rounded p-2 mb-2 yara-builder-string-row" data-string-index="${index}">
                <div class="form-row align-items-end">
                    <div class="col-md-7 mb-2 mb-md-0">
                        <label class="small font-weight-bold mb-1">Text to detect</label>
                        <input type="text" class="form-control yara-builder-string-text" placeholder="Example: powershell">
                    </div>
                    <div class="col-md-3">
                        <div class="custom-control custom-checkbox">
                            <input type="checkbox" class="custom-control-input yara-builder-string-nocase" id="yara_builder_nocase_${index}">
                            <label class="custom-control-label small" for="yara_builder_nocase_${index}">Case insensitive</label>
                        </div>
                        <div class="custom-control custom-checkbox mt-1">
                            <input type="checkbox" class="custom-control-input yara-builder-string-fullword" id="yara_builder_fullword_${index}">
                            <label class="custom-control-label small" for="yara_builder_fullword_${index}">Full word</label>
                        </div>
                    </div>
                    <div class="col-md-2 text-md-right mt-2 mt-md-0">
                        <button type="button" class="btn btn-outline-danger btn-sm yara-builder-remove-string-btn">Remove</button>
                    </div>
                </div>
                <small class="form-text text-muted">Case insensitive: Match regardless of uppercase/lowercase. Full word: Match only the exact word.</small>
            </div>
        `;
    }

    function todayAsIsoDate() {
        return new Date().toISOString().slice(0, 10);
    }

    window.initYaraRuleBuilder = function initYaraRuleBuilder(options) {
        const onRuleGenerated = options.onRuleGenerated;

        const stringsList = document.getElementById('yara_builder_strings_list');
        const addStringButton = document.getElementById('yara_builder_add_string_btn');
        const generateButton = document.getElementById('yara_builder_generate_btn');
        const errorBox = document.getElementById('yara_builder_error');
        const dateField = document.getElementById('yara_builder_date');
        const builderCard = document.getElementById('yara_rule_builder_card');
        const openButton = document.getElementById('yara_builder_open_btn');
        const closeButton = document.getElementById('yara_builder_close_btn');

        let nextStringIndex = 1;

        function setError(message) {
            if (!message) {
                errorBox.textContent = '';
                errorBox.classList.add('d-none');
                return;
            }
            errorBox.textContent = message;
            errorBox.classList.remove('d-none');
        }

        function addStringField() {
            stringsList.insertAdjacentHTML('beforeend', createStringRow(nextStringIndex));
            nextStringIndex += 1;
            updateRemoveButtonsState();
        }

        function updateRemoveButtonsState() {
            const rows = stringsList.querySelectorAll('.yara-builder-string-row');
            const disableRemove = rows.length === 1;
            rows.forEach((row) => {
                const removeButton = row.querySelector('.yara-builder-remove-string-btn');
                removeButton.disabled = disableRemove;
            });
        }

        function validRuleName(ruleName) {
            return /^[A-Za-z_][A-Za-z0-9_]*$/.test(ruleName);
        }

        function buildRule() {
            const ruleName = document.getElementById('yara_builder_rule_name').value.trim();
            const description = document.getElementById('yara_builder_description').value.trim();
            const author = document.getElementById('yara_builder_author').value.trim();
            const date = document.getElementById('yara_builder_date').value.trim();
            const version = document.getElementById('yara_builder_version').value.trim();
            const mode = document.querySelector('input[name="yara_builder_match_mode"]:checked').value;

            if (!ruleName) {
                throw new Error('Rule name is required.');
            }
            if (!validRuleName(ruleName)) {
                throw new Error('Invalid rule name. Use letters, numbers, and underscores only, and start with a letter or underscore.');
            }

            const rows = Array.from(stringsList.querySelectorAll('.yara-builder-string-row'));
            if (rows.length === 0) {
                throw new Error('At least one detection string is required.');
            }

            const detectionLines = rows.map((row, index) => {
                const textValue = row.querySelector('.yara-builder-string-text').value.trim();
                if (!textValue) {
                    throw new Error('Detection strings cannot be empty.');
                }
                const flags = [];
                if (row.querySelector('.yara-builder-string-nocase').checked) {
                    flags.push('nocase');
                }
                if (row.querySelector('.yara-builder-string-fullword').checked) {
                    flags.push('fullword');
                }
                const suffix = flags.length ? ` ${flags.join(' ')}` : '';
                return `        $s${index + 1} = "${escapeYaraString(textValue)}"${suffix}`;
            });

            const meta = [];
            if (description) meta.push(`        description = "${escapeYaraString(description)}"`);
            if (author) meta.push(`        author = "${escapeYaraString(author)}"`);
            if (date) meta.push(`        date = "${escapeYaraString(date)}"`);
            if (version) meta.push(`        version = "${escapeYaraString(version)}"`);

            const lines = [];
            lines.push(`rule ${ruleName} {`);
            if (meta.length) {
                lines.push('    meta:');
                lines.push(...meta);
                lines.push('');
            }
            lines.push('    strings:');
            lines.push(...detectionLines);
            lines.push('');
            lines.push('    condition:');
            lines.push(`        ${mode === 'all' ? 'all of them' : 'any of them'}`);
            lines.push('}');

            return lines.join('\n');
        }


        function openBuilder() {
            builderCard.classList.remove('d-none');
            if (openButton) {
                openButton.classList.add('d-none');
            }
        }

        function closeBuilder() {
            builderCard.classList.add('d-none');
            if (openButton) {
                openButton.classList.remove('d-none');
            }
        }

        if (openButton) {
            openButton.addEventListener('click', function () {
                openBuilder();
            });
        }

        if (closeButton) {
            closeButton.addEventListener('click', function () {
                closeBuilder();
            });
        }

        addStringButton.addEventListener('click', function () {
            addStringField();
        });

        stringsList.addEventListener('click', function (event) {
            if (!event.target.classList.contains('yara-builder-remove-string-btn')) return;
            const rows = stringsList.querySelectorAll('.yara-builder-string-row');
            if (rows.length <= 1) return;
            event.target.closest('.yara-builder-string-row').remove();
            updateRemoveButtonsState();
        });

        generateButton.addEventListener('click', function () {
            setError('');
            try {
                const ruleContent = buildRule();
                onRuleGenerated(ruleContent);
                closeBuilder();
            } catch (error) {
                setError(error.message || 'Unable to generate rule.');
            }
        });

        if (!dateField.value.trim()) {
            dateField.value = todayAsIsoDate();
        }

        addStringField();
    };
})();
