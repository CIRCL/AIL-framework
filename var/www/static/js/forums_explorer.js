document.addEventListener('DOMContentLoaded', () => {
    document.getElementById('page-Forums-Explorer')?.classList.add('active');
    document.querySelectorAll('[data-forum-banner]').forEach(image => {
        const showBanner = () => {
            image.classList.add('is-loaded');
        };
        if (image.complete && image.naturalWidth > 0) {
            showBanner();
        } else {
            image.addEventListener('load', showBanner, {once: true});
        }
    });
    const investigationsToggle = document.getElementById('thread-investigations-toggle');
    const investigationsModal = document.getElementById('investigations_register_obj_modal');
    if (investigationsToggle && investigationsModal) {
        $(investigationsModal).on('hidden.bs.modal', () => investigationsToggle.focus());
    }
    document.querySelectorAll('.forum-translate-names').forEach(button => {
        button.addEventListener('click', async () => {
            const status = document.querySelector('.forum-translation-status');
            const formData = new URLSearchParams({id: button.dataset.objectId});
            if (button.dataset.objectSubtype) {
                formData.set('subtype', button.dataset.objectSubtype);
            }
            button.disabled = true;
            status.textContent = 'Translating names…';
            try {
                const response = await fetch(button.dataset.translationUrl, {
                    method: 'POST',
                    headers: {'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8'},
                    credentials: 'same-origin',
                    body: formData.toString()
                });
                if (!response.ok) {
                    throw new Error('Translation request failed');
                }
                const data = await response.json();
                const pending = [...data.names];
                const translations = new Map();
                while (pending.length) {
                    const entry = pending.pop();
                    if (entry.name_translation) {
                        translations.set(JSON.stringify([entry.type, entry.subtype || '', String(entry.id)]), entry.name_translation);
                    }
                    pending.push(...(entry.child_subforums || []));
                    if (entry.last_post?.thread) {
                        pending.push(entry.last_post.thread);
                    }
                }
                document.querySelectorAll('.forum-name-translation').forEach(element => {
                    const key = JSON.stringify([element.dataset.objectType, element.dataset.objectSubtype || '', element.dataset.objectId]);
                    if (translations.has(key)) {
                        element.textContent = translations.get(key);
                        element.hidden = false;
                    }
                });
                status.textContent = '';
            } catch (error) {
                status.textContent = 'Names could not be translated. Please try again.';
            } finally {
                button.disabled = false;
            }
        });
    });
});
