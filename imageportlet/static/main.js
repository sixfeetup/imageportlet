/**
 * Your Javascript code goes here.
 *
 * This file is deployed as ++resource++youraddon/main.js on your site
 * and automatically included in merge bundles via jsregistry.xml.
 *
 * More info
 *
 * http://collective-docs.readthedocs.org/en/latest/templates_css_and_javascripts/javascript.html
 *
 */

 /*global window,document*/

(function($) { $(function() {
    // check for touch device
    if (!("ontouchstart" in document.documentElement)) {
    document.documentElement.className += " no-touch";
    }
    // apply hover effect only to devices without touch
    $(".no-touch .imagePortlet").hover(
        function() {
            $(this).find(".default").fadeOut();
            $(this).find(".hover").fadeIn();
        }, function() {
            $(this).find(".hover").fadeOut();
            $(this).find(".default").fadeIn();
        }
    );
}); })(jQuery);
