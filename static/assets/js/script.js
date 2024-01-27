'use strict';

// navbar variables
const nav = document.querySelector('.mobile-nav');
const navMenuBtn = document.querySelector('.nav-menu-btn');
const navCloseBtn = document.querySelector('.nav-close-btn');

// theme toggle variables
const themeBtn = document.querySelectorAll('.theme-btn');
const themeBody = document.body;

// Check if the user has a theme preference stored in local storage
const storedTheme = localStorage.getItem('theme');
if (storedTheme) {
  themeBody.classList.add(storedTheme);
}

// Function to toggle the theme
const toggleTheme = function () {
  themeBody.classList.toggle('light-theme');
  themeBody.classList.toggle('dark-theme');

  for (let i = 0; i < themeBtn.length; i++) {
    themeBtn[i].classList.toggle('light');
    themeBtn[i].classList.toggle('dark');
  }

  // Store the user's theme preference in local storage
  const currentTheme = themeBody.classList.contains('dark-theme') ? 'dark-theme' : 'light-theme';
  localStorage.setItem('theme', currentTheme);
};

// Event listeners for theme toggle buttons
for (let i = 0; i < themeBtn.length; i++) {
  themeBtn[i].addEventListener('click', toggleTheme);
}

// navToggle function
const navToggleFunc = function () {
  nav.classList.toggle('active');
};

navMenuBtn.addEventListener('click', navToggleFunc);
navCloseBtn.addEventListener('click', navToggleFunc);
