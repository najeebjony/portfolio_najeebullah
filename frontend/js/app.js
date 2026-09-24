/**
 * Official Portfolio JavaScript - Najeeb Ullah
 * Pure Vanilla JavaScript (No frameworks, zero external dependencies)
 */

document.addEventListener('DOMContentLoaded', () => {
  initTheme();
  initNavigation();
  initDynamicData();
  initContactForm();
  updateCopyrightYear();
});

/* ---------------------------------------------------------
   1. Theme Management (Light / Dark)
--------------------------------------------------------- */
function initTheme() {
  const themeToggle = document.getElementById('theme-toggle');
  let currentTheme = 'light';

  try {
    const savedTheme = localStorage.getItem('nu_portfolio_theme');
    if (savedTheme) {
      currentTheme = savedTheme;
    } else if (window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches) {
      currentTheme = 'dark';
    }
  } catch (e) {
    console.warn('localStorage not accessible for theme persistence:', e);
  }

  document.documentElement.setAttribute('data-theme', currentTheme);

  if (themeToggle) {
    themeToggle.addEventListener('click', () => {
      const active = document.documentElement.getAttribute('data-theme');
      const newTheme = active === 'dark' ? 'light' : 'dark';
      document.documentElement.setAttribute('data-theme', newTheme);
      try {
        localStorage.setItem('nu_portfolio_theme', newTheme);
      } catch (e) {
        console.warn('Unable to save theme in localStorage:', e);
      }
    });
  }
}

/* ---------------------------------------------------------
   2. Responsive Navigation & Smooth Scrolling
--------------------------------------------------------- */
function initNavigation() {
  const menuToggle = document.getElementById('menu-toggle');
  const navMenu = document.getElementById('nav-menu');
  const navLinks = document.querySelectorAll('.nav-link');

  if (menuToggle && navMenu) {
    menuToggle.addEventListener('click', () => {
      const isOpen = navMenu.classList.toggle('open');
      menuToggle.setAttribute('aria-expanded', String(isOpen));
    });

    // Close mobile menu when clicking outside
    document.addEventListener('click', (e) => {
      if (!navMenu.contains(e.target) && !menuToggle.contains(e.target) && navMenu.classList.contains('open')) {
        navMenu.classList.remove('open');
        menuToggle.setAttribute('aria-expanded', 'false');
      }
    });
  }

  // Active section indicator and closing mobile menu on link click
  navLinks.forEach(link => {
    link.addEventListener('click', () => {
      if (navMenu && navMenu.classList.contains('open')) {
        navMenu.classList.remove('open');
        if (menuToggle) menuToggle.setAttribute('aria-expanded', 'false');
      }
    });
  });

  // Highlight active link based on scroll position
  const sections = document.querySelectorAll('section[id]');
  window.addEventListener('scroll', () => {
    const scrollY = window.pageYOffset;
    sections.forEach(section => {
      const sectionHeight = section.offsetHeight;
      const sectionTop = section.offsetTop - 120;
      const sectionId = section.getAttribute('id');
      const correspondingLink = document.querySelector(`.nav-link[href="#${sectionId}"]`);

      if (correspondingLink && scrollY >= sectionTop && scrollY < sectionTop + sectionHeight) {
        navLinks.forEach(l => l.classList.remove('active'));
        correspondingLink.classList.add('active');
      }
    });
  }, { passive: true });
}

/* ---------------------------------------------------------
   3. Dynamic Data Loading (Profile & Projects)
--------------------------------------------------------- */
async function initDynamicData() {
  await loadProfile();
  await loadProjects();
}

async function loadProfile() {
  try {
    const res = await fetch('/api/profile');
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const data = await res.json();

    // Populate Hero texts
    if (data.name) {
      const heroName = document.getElementById('hero-name');
      if (heroName) heroName.textContent = data.name;
    }
    if (data.headline) {
      const heroHeadline = document.getElementById('hero-headline');
      if (heroHeadline) heroHeadline.textContent = data.headline;
    }

    // Handle Profile Image vs Initials
    const heroImg = document.getElementById('hero-img');
    const heroInitials = document.getElementById('hero-initials');
    if (data.images && data.images.has_profile_photo && heroImg) {
      heroImg.onload = () => {
        heroImg.classList.remove('hidden');
        if (heroInitials) heroInitials.classList.add('hidden');
      };
      heroImg.onerror = () => {
        heroImg.classList.add('hidden');
        if (heroInitials) heroInitials.classList.remove('hidden');
      };
      heroImg.src = data.images.profile_photo_url;
      if (heroImg.complete && heroImg.naturalWidth > 0) {
        heroImg.classList.remove('hidden');
        if (heroInitials) heroInitials.classList.add('hidden');
      }
    } else {
      if (heroImg) heroImg.classList.add('hidden');
      if (heroInitials) heroInitials.classList.remove('hidden');
    }

    // Handle GitHub link (hide if null)
    const githubLink = document.getElementById('hero-github-link');
    if (githubLink) {
      if (data.github) {
        githubLink.href = data.github;
        githubLink.classList.remove('hidden');
      } else {
        githubLink.classList.add('hidden');
      }
    }

    // Handle Gallery Setup if photos exist
    if (data.images && data.images.gallery_images && data.images.gallery_images.length > 0) {
      renderGallery(data.images.gallery_images);
    }
  } catch (err) {
    console.error('Error fetching profile:', err);
  }
}

async function loadProjects() {
  const container = document.getElementById('projects-grid');
  if (!container) return;

  try {
    const res = await fetch('/api/projects');
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const projects = await res.json();

    container.innerHTML = '';
    projects.forEach(project => {
      const card = createProjectCard(project);
      container.appendChild(card);
    });
  } catch (err) {
    console.error('Error loading projects:', err);
    container.innerHTML = '<p class="error-msg">Failed to load projects. Please try refreshing.</p>';
  }
}

function createProjectCard(p) {
  const card = document.createElement('article');
  card.className = 'project-card';
  card.id = `project-${p.slug}`;

  // Tech stack chips HTML
  const chipsHtml = (p.tech_stack || []).map(tech => `<span class="chip">${escapeHtml(tech)}</span>`).join('');

  // Live button or disabled label
  let actionBtnHtml = '';
  if (p.live_url) {
    actionBtnHtml = `
      <a href="${escapeHtml(p.live_url)}" target="_blank" rel="noopener noreferrer" class="btn btn-primary btn-open-app">
        Open Live App
        <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <line x1="7" y1="17" x2="17" y2="7"></line>
          <polyline points="7 7 17 7 17 17"></polyline>
        </svg>
      </a>
    `;
  } else {
    actionBtnHtml = `<span class="btn-disabled">Live demo coming soon</span>`;
  }

  // Key Metrics rows
  let metricsRows = '';
  if (p.metrics) {
    if (p.metrics.accuracy) metricsRows += `<tr><th>Accuracy</th><td>${p.metrics.accuracy}</td></tr>`;
    if (p.metrics.precision) metricsRows += `<tr><th>Precision</th><td>${p.metrics.precision}</td></tr>`;
    if (p.metrics.recall) metricsRows += `<tr><th>Recall</th><td>${p.metrics.recall}</td></tr>`;
    if (p.metrics.f1) metricsRows += `<tr><th>F1-Score</th><td>${p.metrics.f1}</td></tr>`;
    if (p.metrics.roc_auc) metricsRows += `<tr><th>ROC-AUC</th><td>${p.metrics.roc_auc}</td></tr>`;
    if (p.metrics.test_cohort) metricsRows += `<tr><th>Cohort</th><td>${p.metrics.test_cohort}</td></tr>`;
  }

  // Cross Validation display
  let cvHtml = '';
  if (p.cross_validation) {
    cvHtml = `
      <div class="cv-highlight">
        <strong>Cross-Validation:</strong> ${escapeHtml(p.cross_validation)}
        ${p.cross_validation_note ? `<br><small>${escapeHtml(p.cross_validation_note)}</small>` : ''}
      </div>
    `;
  }

  // Honest Note display (e.g. for Diabetes project)
  let honestNoteHtml = '';
  if (p.honest_note) {
    honestNoteHtml = `
      <div class="honest-note">
        <strong>Technical Note:</strong> ${escapeHtml(p.honest_note)}
      </div>
    `;
  }

  // Confusion matrix display
  let cmHtml = '';
  if (p.confusion_matrix) {
    cmHtml = `
      <div style="margin-top: 0.75rem;">
        <span class="meta-field-label">Confusion Matrix (Holdout RF):</span>
        <code class="confusion-matrix-display">${JSON.stringify(p.confusion_matrix)}</code>
      </div>
    `;
  }

  // Other models compared
  let otherModelsHtml = '';
  if (p.other_models && p.other_models.length > 0) {
    const list = p.other_models.map(m => `<li>${escapeHtml(m.model)}: <strong>${escapeHtml(m.test_accuracy)}</strong></li>`).join('');
    otherModelsHtml = `
      <div class="details-box">
        <h4 class="details-box-title">Other Models Tested</h4>
        <ul class="features-list">${list}</ul>
      </div>
    `;
  }

  // Features breakdown (e.g. Breast cancer)
  let featuresBreakdownHtml = '';
  if (p.features) {
    const num = (p.features.numeric || []).join(', ');
    const cat = (p.features.categorical || []).join(', ');
    featuresBreakdownHtml = `
      <div class="details-box">
        <h4 class="details-box-title">Clinical Feature Space</h4>
        <p style="font-size:0.875rem; margin-bottom: 0.5rem;"><strong>Numeric:</strong> ${escapeHtml(num)}</p>
        <p style="font-size:0.875rem;"><strong>Categorical:</strong> ${escapeHtml(cat)}</p>
      </div>
    `;
  }

  // App Features list
  let appFeaturesHtml = '';
  if (p.app_features && p.app_features.length > 0) {
    const featItems = p.app_features.map(f => `<li>${escapeHtml(f)}</li>`).join('');
    appFeaturesHtml = `
      <div class="details-box">
        <h4 class="details-box-title">Application Capabilities</h4>
        <ul class="features-list">${featItems}</ul>
      </div>
    `;
  }

  card.innerHTML = `
    <div class="project-card-header">
      <div>
        <h3 class="project-title">${escapeHtml(p.title)}</h3>
      </div>
      <div class="project-headline-badge">${escapeHtml(p.headline_stat)}</div>
    </div>

    <p class="project-summary">${escapeHtml(p.one_line_summary)}</p>

    <div class="project-meta-grid">
      <div>
        <span class="meta-field-label">Dataset</span>
        <span class="meta-field-value">${escapeHtml(p.dataset)}</span>
      </div>
      <div>
        <span class="meta-field-label">Champion Model</span>
        <span class="meta-field-value">${escapeHtml(p.champion_model)}</span>
      </div>
      <div>
        <span class="meta-field-label">Models Evaluated</span>
        <span class="meta-field-value">${escapeHtml(p.models_compared)}</span>
      </div>
    </div>

    <div class="project-chips-wrapper">
      <span class="chips-label">Technologies</span>
      <div class="chip-container">${chipsHtml}</div>
    </div>

    <div class="project-actions">
      ${actionBtnHtml}
      <button type="button" class="btn-toggle-details" aria-expanded="false" aria-controls="details-${p.slug}">
        <span>View Details</span>
        <svg class="toggle-arrow" xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <polyline points="6 9 12 15 18 9"></polyline>
        </svg>
      </button>
    </div>

    <div class="project-details-panel" id="details-${p.slug}">
      <div class="details-grid">
        <div class="details-box">
          <h4 class="details-box-title">Verified Model Metrics</h4>
          <table class="metrics-table">
            <tbody>${metricsRows}</tbody>
          </table>
          ${cvHtml}
          ${honestNoteHtml}
          ${cmHtml}
        </div>
        ${otherModelsHtml}
        ${featuresBreakdownHtml}
        ${appFeaturesHtml}
      </div>
      <p class="project-disclaimer">${escapeHtml(p.disclaimer)}</p>
    </div>
  `;

  // Attach accordion event
  const toggleBtn = card.querySelector('.btn-toggle-details');
  const detailsPanel = card.querySelector('.project-details-panel');
  toggleBtn.addEventListener('click', () => {
    const isExpanded = toggleBtn.getAttribute('aria-expanded') === 'true';
    toggleBtn.setAttribute('aria-expanded', String(!isExpanded));
    detailsPanel.classList.toggle('open', !isExpanded);
    toggleBtn.querySelector('span').textContent = isExpanded ? 'View Details' : 'Hide Details';
  });

  return card;
}

/* ---------------------------------------------------------
   4. Gallery & Lightbox
--------------------------------------------------------- */
let galleryItems = [];
let currentLightboxIdx = 0;

function renderGallery(images) {
  galleryItems = images;
  const gallerySection = document.getElementById('gallery');
  const galleryNavItem = document.getElementById('gallery-nav-item');
  const galleryGrid = document.getElementById('gallery-grid');

  if (!gallerySection || !galleryNavItem || !galleryGrid) return;

  gallerySection.classList.remove('section-hidden');
  galleryNavItem.classList.remove('nav-item-hidden');
  galleryGrid.innerHTML = '';

  images.forEach((img, index) => {
    const card = document.createElement('div');
    card.className = 'gallery-card';
    card.setAttribute('role', 'button');
    card.setAttribute('tabindex', '0');
    card.setAttribute('aria-label', `View ${img.alt}`);
    card.innerHTML = `<img src="${escapeHtml(img.url)}" alt="${escapeHtml(img.alt)}" loading="lazy" width="400" height="300">`;

    card.addEventListener('click', () => openLightbox(index));
    card.addEventListener('keydown', (e) => {
      if (e.key === 'Enter' || e.key === ' ') {
        e.preventDefault();
        openLightbox(index);
      }
    });

    galleryGrid.appendChild(card);
  });

  initLightboxControls();
}

function initLightboxControls() {
  const lightbox = document.getElementById('lightbox');
  const closeBtn = document.getElementById('lightbox-close');
  const prevBtn = document.getElementById('lightbox-prev');
  const nextBtn = document.getElementById('lightbox-next');

  if (!lightbox) return;

  closeBtn.addEventListener('click', closeLightbox);
  prevBtn.addEventListener('click', prevLightbox);
  nextBtn.addEventListener('click', nextLightbox);

  lightbox.addEventListener('click', (e) => {
    if (e.target === lightbox) {
      closeLightbox();
    }
  });

  document.addEventListener('keydown', (e) => {
    if (!lightbox.classList.contains('active')) return;
    if (e.key === 'Escape') closeLightbox();
    if (e.key === 'ArrowLeft') prevLightbox();
    if (e.key === 'ArrowRight') nextLightbox();
  });
}

function openLightbox(index) {
  const lightbox = document.getElementById('lightbox');
  const lightboxImg = document.getElementById('lightbox-img');
  const lightboxCaption = document.getElementById('lightbox-caption');

  if (!lightbox || !galleryItems[index]) return;

  currentLightboxIdx = index;
  const item = galleryItems[index];

  lightboxImg.src = item.url;
  lightboxImg.alt = item.alt;
  lightboxCaption.textContent = item.alt;

  lightbox.hidden = false;
  requestAnimationFrame(() => {
    lightbox.classList.add('active');
  });
  document.body.style.overflow = 'hidden';
}

function closeLightbox() {
  const lightbox = document.getElementById('lightbox');
  if (!lightbox) return;

  lightbox.classList.remove('active');
  setTimeout(() => {
    lightbox.hidden = true;
    document.body.style.overflow = '';
  }, 250);
}

function prevLightbox() {
  if (galleryItems.length === 0) return;
  currentLightboxIdx = (currentLightboxIdx - 1 + galleryItems.length) % galleryItems.length;
  updateLightboxContent();
}

function nextLightbox() {
  if (galleryItems.length === 0) return;
  currentLightboxIdx = (currentLightboxIdx + 1) % galleryItems.length;
  updateLightboxContent();
}

function updateLightboxContent() {
  const item = galleryItems[currentLightboxIdx];
  const lightboxImg = document.getElementById('lightbox-img');
  const lightboxCaption = document.getElementById('lightbox-caption');

  if (lightboxImg && item) {
    lightboxImg.src = item.url;
    lightboxImg.alt = item.alt;
    if (lightboxCaption) lightboxCaption.textContent = item.alt;
  }
}

/* ---------------------------------------------------------
   5. Contact Form Validation & Submission
--------------------------------------------------------- */
function initContactForm() {
  const form = document.getElementById('contact-form');
  const statusEl = document.getElementById('form-status');
  const submitBtn = document.getElementById('submit-btn');
  const btnText = submitBtn ? submitBtn.querySelector('.btn-text') : null;
  const btnSpinner = submitBtn ? submitBtn.querySelector('.btn-spinner') : null;

  if (!form) return;

  form.addEventListener('submit', async (e) => {
    e.preventDefault();

    // Reset status and errors
    clearFormErrors();
    statusEl.className = 'form-status';
    statusEl.textContent = '';

    const name = form.name.value.trim();
    const email = form.email.value.trim();
    const subject = form.subject.value.trim();
    const message = form.message.value.trim();
    const website = form.website.value.trim(); // honeypot

    // Client-side validation
    let hasError = false;

    if (name.length < 2 || name.length > 80) {
      setFieldError('name-error', 'Name must be between 2 and 80 characters.');
      form.name.classList.add('is-invalid');
      hasError = true;
    }

    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(email)) {
      setFieldError('email-error', 'Please enter a valid email address.');
      form.email.classList.add('is-invalid');
      hasError = true;
    }

    if (subject.length < 1 || subject.length > 120) {
      setFieldError('subject-error', 'Subject is required (max 120 characters).');
      form.subject.classList.add('is-invalid');
      hasError = true;
    }

    if (message.length < 10 || message.length > 2000) {
      setFieldError('message-error', 'Message must be between 10 and 2000 characters.');
      form.message.classList.add('is-invalid');
      hasError = true;
    }

    if (hasError) return;

    // Loading UI state
    submitBtn.disabled = true;
    if (btnText) btnText.textContent = 'Sending...';
    if (btnSpinner) btnSpinner.classList.remove('hidden');

    try {
      const response = await fetch('/api/contact', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name, email, subject, message, website })
      });

      const data = await response.json();

      if (response.ok) {
        statusEl.className = 'form-status success';
        statusEl.textContent = data.message || 'Thank you! Your message has been sent successfully.';
        form.reset();
      } else {
        statusEl.className = 'form-status error';
        if (response.status === 429) {
          statusEl.textContent = 'Submission limit reached (max 5 per hour). Please try again later.';
        } else if (data.detail) {
          const detailMsg = Array.isArray(data.detail) 
            ? data.detail.map(d => d.msg).join(', ') 
            : data.detail;
          statusEl.textContent = detailMsg || 'Failed to submit form. Please verify your entries.';
        } else {
          statusEl.textContent = 'An error occurred while submitting your message. Please try again.';
        }
      }
    } catch (err) {
      console.error('Submission error:', err);
      statusEl.className = 'form-status error';
      statusEl.textContent = 'Network error: Unable to reach the server. Please check your connection.';
    } finally {
      submitBtn.disabled = false;
      if (btnText) btnText.textContent = 'Send Message';
      if (btnSpinner) btnSpinner.classList.add('hidden');
    }
  });

  function clearFormErrors() {
    ['name-error', 'email-error', 'subject-error', 'message-error'].forEach(id => {
      const el = document.getElementById(id);
      if (el) el.textContent = '';
    });
    ['contact-name', 'contact-email', 'contact-subject', 'contact-message'].forEach(id => {
      const input = document.getElementById(id);
      if (input) input.classList.remove('is-invalid');
    });
  }

  function setFieldError(elementId, msg) {
    const el = document.getElementById(elementId);
    if (el) el.textContent = msg;
  }
}

/* ---------------------------------------------------------
   6. Utilities
--------------------------------------------------------- */
function updateCopyrightYear() {
  const yearEl = document.getElementById('copyright-year');
  if (yearEl) {
    yearEl.textContent = new Date().getFullYear();
  }
}

function escapeHtml(str) {
  if (!str) return '';
  const div = document.createElement('div');
  div.textContent = str;
  return div.innerHTML;
}
