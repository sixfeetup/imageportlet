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
    $(".imagePortlet").hover(
        function() {
            $(this).find(".default").fadeOut();
            $(this).find(".hover").fadeIn();
        }, function() {
            $(this).find(".hover").fadeOut();
            $(this).find(".default").fadeIn();
        }
    );
}); })(jQuery);
