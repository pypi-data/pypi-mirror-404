/* Auto-submit GPWebPay redirect form when JS is allowed by CSP. */
(function () {
  var form = document.getElementById('gpwebpay-form');
  if (form) {
    form.submit();
  }
})();
