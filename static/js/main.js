// Main JavaScript file for the Instagram Repost Bot

document.addEventListener('DOMContentLoaded', function() {
  // Initialize feather icons
  if (typeof feather !== 'undefined') {
    feather.replace();
  }
  
  // Initialize tooltips
  const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
  tooltipTriggerList.forEach(function(tooltipTriggerEl) {
    new bootstrap.Tooltip(tooltipTriggerEl);
  });
  
  // Auto-dismiss alerts after 5 seconds
  const alerts = document.querySelectorAll('.alert:not(.alert-permanent)');
  alerts.forEach(function(alert) {
    setTimeout(function() {
      const bsAlert = new bootstrap.Alert(alert);
      bsAlert.close();
    }, 5000);
  });
  
  // Handle status filter changes on history page
  const statusFilter = document.getElementById('status');
  const daysFilter = document.getElementById('days');
  
  if (statusFilter && daysFilter) {
    statusFilter.addEventListener('change', function() {
      this.closest('form').submit();
    });
    
    daysFilter.addEventListener('change', function() {
      this.closest('form').submit();
    });
  }
  
  // Toggle elements based on checkbox state
  const autoRepostCheckbox = document.getElementById('auto_repost');
  const addCreditCheckbox = document.getElementById('add_credit');
  
  if (autoRepostCheckbox) {
    const relatedElements = document.querySelectorAll('#repost_delay, #check_interval, #post_limit_per_day');
    
    function toggleRelatedElements() {
      const isEnabled = autoRepostCheckbox.checked;
      relatedElements.forEach(function(element) {
        element.disabled = !isEnabled;
        element.parentElement.classList.toggle('text-muted', !isEnabled);
      });
    }
    
    autoRepostCheckbox.addEventListener('change', toggleRelatedElements);
    toggleRelatedElements(); // Initial state
  }
  
  if (addCreditCheckbox) {
    const creditTextInput = document.getElementById('credit_text');
    
    function toggleCreditText() {
      if (creditTextInput) {
        creditTextInput.disabled = !addCreditCheckbox.checked;
        creditTextInput.parentElement.classList.toggle('text-muted', !addCreditCheckbox.checked);
      }
    }
    
    addCreditCheckbox.addEventListener('change', toggleCreditText);
    toggleCreditText(); // Initial state
  }
});
