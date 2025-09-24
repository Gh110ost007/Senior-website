// Mobile nav toggle
const navToggle = document.querySelector('.nav-toggle');
const navLinks = document.querySelector('#nav-links');
if (navToggle && navLinks) {
  navToggle.addEventListener('click', () => {
    const expanded = navToggle.getAttribute('aria-expanded') === 'true';
    navToggle.setAttribute('aria-expanded', String(!expanded));
    navLinks.classList.toggle('open');
  });
}

// Footer year
const yearEl = document.getElementById('year');
if (yearEl) {
  yearEl.textContent = new Date().getFullYear();
}

// Analytics and Event Logging
const sessionId = 'session_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
const userId = localStorage.getItem('user_id') || 'anonymous_' + Math.random().toString(36).substr(2, 9);

// Store user ID for future sessions
if (!localStorage.getItem('user_id')) {
  localStorage.setItem('user_id', userId);
}

function logEvent(eventType, metadata = {}) {
  fetch('/api/log', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      event_type: eventType,
      session_id: sessionId,
      user_id: userId,
      metadata: metadata
    })
  }).catch(err => console.log('Analytics error:', err));
}

// Track page views
logEvent('page_view', {
  page: window.location.pathname,
  referrer: document.referrer
});

// Track button clicks
document.addEventListener('click', function(e) {
  if (e.target.matches('a[href*="contact"]')) {
    logEvent('contact_click', { source: e.target.textContent });
  }
  if (e.target.matches('a[href*="seminar"]')) {
    logEvent('seminar_click', { source: e.target.textContent });
  }
  if (e.target.matches('.btn-primary')) {
    logEvent('cta_click', { button_text: e.target.textContent });
  }
  if (e.target.matches('.complete-btn')) {
    const lessonId = e.target.getAttribute('data-lesson-id');
    toggleLessonComplete(lessonId, e.target);
  }
});

// Track testimonial navigation
function trackTestimonialChange(direction) {
  logEvent('testimonial_navigate', { direction: direction > 0 ? 'next' : 'previous' });
}

// Track form submissions
document.addEventListener('submit', function(e) {
  if (e.target.matches('form')) {
    logEvent('form_submit', { form_id: e.target.id || 'unknown' });
  }
});

// Track time spent on page
let startTime = Date.now();
window.addEventListener('beforeunload', function() {
  const timeSpent = Math.round((Date.now() - startTime) / 1000);
  logEvent('page_time_spent', { 
    page: window.location.pathname,
    seconds: timeSpent 
  });
});

// Progress Tracking System
function toggleLessonComplete(lessonId, button) {
  const lessonItem = button.closest('.lesson-item');
  const isCompleted = lessonItem.classList.contains('completed');
  
  // Toggle visual state
  if (isCompleted) {
    lessonItem.classList.remove('completed');
    button.classList.remove('completed');
    button.querySelector('.complete-text').textContent = 'Mark Complete';
  } else {
    lessonItem.classList.add('completed');
    button.classList.add('completed');
    button.querySelector('.complete-text').textContent = 'Completed';
  }
  
  // Update progress bar
  updateProgressBar(lessonItem.closest('.topic-card'));
  
  // Send to backend
  updateLessonProgress(lessonId, !isCompleted);
  
  // Track analytics
  logEvent('lesson_complete', {
    lesson_id: lessonId,
    completed: !isCompleted
  });
}

function updateProgressBar(topicCard) {
  const completedItems = topicCard.querySelectorAll('.lesson-item.completed').length;
  const totalItems = topicCard.querySelectorAll('.lesson-item').length;
  const percentage = Math.round((completedItems / totalItems) * 100);
  
  // Update progress text
  const progressText = topicCard.querySelector('.progress-text');
  progressText.textContent = `${completedItems}/${totalItems} completed`;
  
  // Update progress bar
  const progressFill = topicCard.querySelector('.progress-fill');
  progressFill.style.width = `${percentage}%`;
}

function updateLessonProgress(lessonId, completed) {
  fetch('/api/progress', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      lesson_id: lessonId,
      completed: completed,
      time_spent: 0 // Could track time spent on each lesson
    })
  }).catch(err => console.log('Progress update error:', err));
}

// Load existing progress on page load
function loadProgress() {
  // This would typically fetch from the backend
  // For now, we'll just initialize the progress bars
  document.querySelectorAll('.topic-card').forEach(card => {
    updateProgressBar(card);
  });
}

// Initialize progress tracking when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
  loadProgress();
});

// Testimonial carousel
let currentTestimonial = 0;
let testimonials = [];
let totalTestimonials = 0;

function initTestimonials() {
  testimonials = document.querySelectorAll('.testimonial-slide');
  totalTestimonials = testimonials.length;
  console.log('Found testimonials:', totalTestimonials);
  
  if (totalTestimonials > 0) {
    showTestimonial(0);
  }
}

function showTestimonial(index) {
  testimonials.forEach((slide, i) => {
    slide.classList.toggle('active', i === index);
  });
}

function changeTestimonial(direction) {
  if (totalTestimonials === 0) return;
  
  // Track testimonial navigation
  trackTestimonialChange(direction);
  
  currentTestimonial += direction;
  
  if (currentTestimonial >= totalTestimonials) {
    currentTestimonial = 0;
  } else if (currentTestimonial < 0) {
    currentTestimonial = totalTestimonials - 1;
  }
  
  showTestimonial(currentTestimonial);
}

// Initialize testimonials when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
  initTestimonials();
  
  // Auto-advance testimonials every 5 seconds
  if (totalTestimonials > 1) {
    setInterval(() => {
      changeTestimonial(1);
    }, 5000);
  }
});

// Preferences: dark mode and font scaling
const root = document.documentElement;
const DARK_KEY = 'prefers-dark';
const FONT_KEY = 'font-scale';

function applyPrefs() {
  const dark = localStorage.getItem(DARK_KEY) === 'true';
  const scale = Number(localStorage.getItem(FONT_KEY) || '1');
  root.classList.toggle('dark', dark);
  root.style.setProperty('--font-scale', String(Math.min(1.4, Math.max(0.9, scale))));
}

applyPrefs();

const toggleDarkBtn = document.getElementById('toggle-dark');
const incBtn = document.getElementById('increase-font');
const decBtn = document.getElementById('decrease-font');

function reflectDarkButton() {
  if (!toggleDarkBtn) return;
  const dark = localStorage.getItem(DARK_KEY) === 'true';
  toggleDarkBtn.setAttribute('aria-pressed', String(dark));
  toggleDarkBtn.textContent = dark ? 'Light mode' : 'Dark mode';
}

if (toggleDarkBtn) {
  toggleDarkBtn.addEventListener('click', () => {
    const next = !(localStorage.getItem(DARK_KEY) === 'true');
    localStorage.setItem(DARK_KEY, String(next));
    applyPrefs();
    reflectDarkButton();
  });
  reflectDarkButton();
}
if (incBtn) {
  incBtn.addEventListener('click', () => {
    const cur = Number(localStorage.getItem(FONT_KEY) || '1');
    localStorage.setItem(FONT_KEY, String(Math.min(1.4, cur + 0.05)));
    applyPrefs();
  });
}
if (decBtn) {
  decBtn.addEventListener('click', () => {
    const cur = Number(localStorage.getItem(FONT_KEY) || '1');
    localStorage.setItem(FONT_KEY, String(Math.max(0.9, cur - 0.05)));
    applyPrefs();
  });
}

// FAQ Accordion
function toggleFAQ(element) {
  const answer = element.nextElementSibling;
  const icon = element.querySelector('.faq-icon');
  const isOpen = answer.classList.contains('open');
  
  // Close all other FAQs
  document.querySelectorAll('.faq-answer').forEach(a => {
    a.classList.remove('open');
    a.previousElementSibling.querySelector('.faq-icon').classList.remove('open');
  });
  
  // Toggle current FAQ
  if (!isOpen) {
    answer.classList.add('open');
    icon.classList.add('open');
  }
}

// Booking form with fetch to /book
const form = document.getElementById('booking-form');
const statusEl = document.getElementById('form-status');
if (form) {
  form.addEventListener('submit', async (e) => {
    e.preventDefault();
    if (statusEl) statusEl.textContent = '';
    
    const submitBtn = form.querySelector('button[type="submit"]');
    submitBtn.classList.add('loading');
    form.classList.add('loading');
    
    const data = new FormData(form);

    const name = String(data.get('name') || '').trim();
    const phone = String(data.get('phone') || '').trim();
    const topic = String(data.get('topic') || '').trim();

    if (!name || !phone || !topic) {
      if (statusEl) statusEl.textContent = 'Please fill required fields.';
      submitBtn.classList.remove('loading');
      form.classList.remove('loading');
      return;
    }

    try {
      const res = await fetch('/book', {
        method: 'POST',
        body: data,
      });
      if (!res.ok) throw new Error('Request failed');
      const json = await res.json();
      if (json.ok) {
        if (statusEl) statusEl.textContent = 'Thanks! We will contact you within 24 hours.';
        form.reset();
      } else {
        if (statusEl) statusEl.textContent = 'There was a problem. Please try again.';
      }
    } catch (err) {
      if (statusEl) statusEl.textContent = 'Network error. Please try again.';
    } finally {
      submitBtn.classList.remove('loading');
      form.classList.remove('loading');
    }
  });
}

// Seminar form with loading state
const seminarForm = document.getElementById('seminar-form');
const seminarStatusEl = document.getElementById('seminar-status');
if (seminarForm) {
  seminarForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    if (seminarStatusEl) seminarStatusEl.textContent = '';
    
    const submitBtn = seminarForm.querySelector('button[type="submit"]');
    submitBtn.classList.add('loading');
    seminarForm.classList.add('loading');
    
    const data = new FormData(seminarForm);

    const org = String(data.get('org') || '').trim();
    const contact = String(data.get('contact') || '').trim();
    const phone = String(data.get('phone') || '').trim();

    if (!org || !contact || !phone) {
      if (seminarStatusEl) seminarStatusEl.textContent = 'Please fill required fields.';
      submitBtn.classList.remove('loading');
      seminarForm.classList.remove('loading');
      return;
    }

    try {
      const res = await fetch('/seminar', {
        method: 'POST',
        body: data,
      });
      if (!res.ok) throw new Error('Request failed');
      const json = await res.json();
      if (json.ok) {
        if (seminarStatusEl) seminarStatusEl.textContent = 'Thanks! We will contact you within 24 hours.';
        seminarForm.reset();
      } else {
        if (seminarStatusEl) seminarStatusEl.textContent = 'There was a problem. Please try again.';
      }
    } catch (err) {
      if (seminarStatusEl) seminarStatusEl.textContent = 'Network error. Please try again.';
    } finally {
      submitBtn.classList.remove('loading');
      seminarForm.classList.remove('loading');
    }
  });
}

// Pricing hover interaction
const pricingCards = document.querySelectorAll('.pricing-card');
if (pricingCards.length) {
  pricingCards.forEach((card) => {
    card.addEventListener('mouseover', () => {
      pricingCards.forEach((c) => c.classList.remove('active'));
      card.classList.add('active');
    });
  });
}

// Testimonial slider logic (uses testimonials JSON embedded in page)
const dataScript = document.getElementById('testimonials-data');
const reviewWrap = document.getElementById('reviewWrap');
const leftArrow = document.getElementById('leftArrow');
const rightArrow = document.getElementById('rightArrow');
const imgDiv = document.getElementById('imgDiv');
const personName = document.getElementById('personName');
const profession = document.getElementById('profession');
const description = document.getElementById('description');
const surpriseMeBtn = null;
const chicken = null;

let testimonialsData = [];
try {
  testimonialsData = dataScript ? JSON.parse(dataScript.textContent || '[]') : [];
} catch (e) {
  testimonialsData = [];
}

let currentPerson = 0;
let isChickenVisible = false;

function setPerson(idx) {
  if (!testimonialsData.length) return;
  const p = testimonialsData[idx % testimonialsData.length];
  // Fallbacks for fields
  const name = p.name || 'Happy Client';
  const role = p.role || '';
  const quote = p.quote || '';
  const photo = p.photo || 'https://via.placeholder.com/240x240.png?text=%F0%9F%98%8A';
  imgDiv.style.backgroundImage = `url('${photo}')`;
  personName.textContent = name;
  profession.textContent = role;
  description.textContent = quote;
}

function slide(whichSide, nextIndex) {
  if (!reviewWrap) return;
  const reviewWrapWidth = reviewWrap.offsetWidth + 'px';
  const side1 = whichSide === 'left' ? '' : '-';
  const side2 = whichSide === 'left' ? '-' : '';
  reviewWrap.style.transition = 'opacity 0.4s, transform 0.4s';
  reviewWrap.style.opacity = '0';
  reviewWrap.style.transform = `translateX(${side1}${reviewWrapWidth})`;
  setTimeout(() => {
    reviewWrap.style.transition = 'none';
    reviewWrap.style.transform = `translateX(${side2}${reviewWrapWidth})`;
    setPerson(nextIndex);
    setTimeout(() => {
      reviewWrap.style.transition = 'opacity 0.4s, transform 0.4s';
      reviewWrap.style.opacity = '1';
      reviewWrap.style.transform = 'translateX(0)';
    }, 10);
  }, 400);
}

if (reviewWrap && testimonialsData.length) {
  setPerson(0);
  if (leftArrow) leftArrow.addEventListener('click', () => {
    currentPerson = (currentPerson + 1) % testimonialsData.length;
    slide('left', currentPerson);
  });
  if (rightArrow) rightArrow.addEventListener('click', () => {
    currentPerson = (currentPerson - 1 + testimonialsData.length) % testimonialsData.length;
    slide('right', currentPerson);
  });
}

// FAQ Accordion functionality
function initAccordion() {
  const items = document.querySelectorAll(".accordion button");

  function toggleAccordion() {
    const itemToggle = this.getAttribute('aria-expanded');
    
    // Close all other accordion items
    for (let i = 0; i < items.length; i++) {
      items[i].setAttribute('aria-expanded', 'false');
    }
    
    // Toggle current item
    if (itemToggle === 'false') {
      this.setAttribute('aria-expanded', 'true');
    }
  }

  items.forEach(item => item.addEventListener('click', toggleAccordion));
}

// Initialize accordion when DOM is loaded
document.addEventListener('DOMContentLoaded', initAccordion);
