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
    const threadDetailsToggle = document.querySelector('.ail-tools-toggle');
    if (threadDetailsToggle) {
        const threadDetails = document.getElementById(threadDetailsToggle.getAttribute('aria-controls'));
        threadDetailsToggle.addEventListener('click', () => {
            threadDetails.hidden = !threadDetails.hidden;
            threadDetailsToggle.setAttribute('aria-expanded', String(!threadDetails.hidden));
        });
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

function setupForumImageVisibility(page) {
    const toolbar = page.querySelector('.reading-toolbar');
    const quickControls = page.querySelector('.compact-blur-bar');
    if (!toolbar || !quickControls) {
        return;
    }

    const sliders = page.querySelectorAll('.visibility-slider');
    const buttons = page.querySelectorAll('[data-image-visibility]');
    const navbar = document.querySelector('.ail-navbar');

    function setImageVisibility(value) {
        const visibility = Number(value);
        const blur = 15 - visibility;
        page.style.setProperty('--object-image-blur', blur + 'px');
        sliders.forEach(slider => {
            slider.value = visibility;
            slider.setAttribute('aria-valuetext', blur === 0 ? 'Images revealed' : blur === 15 ? 'Images hidden' : blur + ' pixel blur');
        });
        buttons.forEach(button => {
            button.setAttribute('aria-pressed', String(Number(button.dataset.imageVisibility) === visibility));
        });
    }

    sliders.forEach(slider => slider.addEventListener('input', () => setImageVisibility(slider.value)));
    buttons.forEach(button => {
        button.addEventListener('click', () => setImageVisibility(button.dataset.imageVisibility));
    });

    function updateQuickControls() {
        const navBottom = navbar ? navbar.getBoundingClientRect().bottom : 0;
        quickControls.hidden = toolbar.getBoundingClientRect().bottom > navBottom;
    }

    let scrollFrame = null;
    window.addEventListener('scroll', () => {
        if (scrollFrame === null) {
            scrollFrame = requestAnimationFrame(() => {
                updateQuickControls();
                scrollFrame = null;
            });
        }
    }, {passive: true});
    const resizeObserver = new ResizeObserver(updateQuickControls);
    resizeObserver.observe(toolbar);
    if (navbar) {
        resizeObserver.observe(navbar);
    }
    window.addEventListener('pageshow', updateQuickControls);
    setImageVisibility(sliders[0].value);
    updateQuickControls();
}

document.addEventListener('DOMContentLoaded', () => {
    const page = document.querySelector('[data-post-translation-url]');
    if (!page) {
        return;
    }

    setupForumImageVisibility(page);

    page.querySelectorAll('[data-language-editor]').forEach(button => {
        const editor = document.getElementById(button.getAttribute('aria-controls'));
        button.addEventListener('click', () => {
            editor.hidden = !editor.hidden;
            button.setAttribute('aria-expanded', String(!editor.hidden));
        });
    });

    page.querySelectorAll('.language-editor select').forEach(select => {
        select.addEventListener('change', () => {
            const textarea = select.form.querySelector('textarea[name="translation"]');
            if (textarea) {
                textarea.value = '';
            }
        });
    });

    function showNameTranslations(data) {
        if (data.thread_name_translation) {
            page.querySelectorAll('.forum-thread-name-translation').forEach(element => {
                element.textContent = data.thread_name_translation;
                element.hidden = false;
            });
        }
        if (data.subforum_name_translation) {
            page.querySelectorAll('.forum-subforum-name-translation').forEach(element => {
                element.textContent = data.subforum_name_translation;
                element.hidden = false;
            });
        }
        if (data.breadcrumb_name_translations) {
            page.querySelectorAll('.forum-breadcrumb-translation').forEach((element, index) => {
                const translation = data.breadcrumb_name_translations[index];
                if (translation) {
                    element.textContent = translation;
                    element.hidden = false;
                }
            });
        }
    }

    page.querySelectorAll('[data-translate-post]').forEach(button => {
        button.addEventListener('click', async () => {
            const article = button.closest('.forum-post');
            const status = article.querySelector('.post-status');
            button.disabled = true;
            button.setAttribute('aria-busy', 'true');
            status.hidden = true;
            try {
                const response = await fetch(page.dataset.postTranslationUrl, {
                    method: 'POST',
                    headers: {'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8'},
                    credentials: 'same-origin',
                    body: new URLSearchParams({id: article.dataset.postId}).toString()
                });
                const data = await response.json();
                if (!response.ok || !data.translation) {
                    throw new Error('No translation was returned. Check your preferred language and try again.');
                }
                article.querySelector('.post-translation-text').textContent = data.translation;
                article.querySelector('.translation').hidden = false;
                showNameTranslations(data);
            } catch (error) {
                status.textContent = 'Unable to translate this post. ' + error.message;
                status.hidden = false;
            } finally {
                button.disabled = false;
                button.removeAttribute('aria-busy');
            }
        });
    });

    page.querySelectorAll('[data-hide-translation]').forEach(button => {
        button.addEventListener('click', () => {
            button.closest('.translation').hidden = true;
        });
    });

    $(page).find('.forum-post [data-toggle="popover"]').popover({boundary: 'window'});
});
