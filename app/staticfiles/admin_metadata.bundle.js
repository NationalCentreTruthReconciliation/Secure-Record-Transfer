/*
 * ATTENTION: An "eval-source-map" devtool has been used.
 * This devtool is neither made for production nor for readable output files.
 * It uses "eval()" calls to create a separate source file with attached SourceMaps in the browser devtools.
 * If you are trying to read the output file, select a different devtool (https://webpack.js.org/configuration/devtool/)
 * or disable the default devtool with "devtool: false".
 * If you are looking for production-ready output files, see mode: "production" (https://webpack.js.org/configuration/mode/).
 */
/******/ (() => { // webpackBootstrap
/******/ 	var __webpack_modules__ = ({

/***/ "./app/caais/static/caais/js/admin/dateOfMaterials.js":
/*!************************************************************!*\
  !*** ./app/caais/static/caais/js/admin/dateOfMaterials.js ***!
  \************************************************************/
/***/ (() => {

eval("/**\n * Apply date mask to the date of materials field using jQuery Mask plugin.\n * Supports both single date (YYYY-MM-DD) and date range (YYYY-MM-DD - YYYY-MM-DD) formats.\n */\n\n/* global django */\n\nconst $ = django.jQuery;\n\n$(document).ready(function() {\n    const dateField = $(\"#id_date_of_materials\");\n\n    // Get the placeholder elements used to indicate that the date is approximate\n    const approxDatePlaceholders = $(\".approx-date-wrapper\");\n  \n    const masks = {\n        singleDate: {\n            pattern: \"Y000-00-00\",\n            options: {\n                clearIfNotMatch: false,\n                placeholder: \"YYYY-MM-DD\",\n                translation: {\n                    Y: {pattern: /[1-9]/},\n                }\n            }\n        },\n        dateRange: {\n            pattern: \"Y000-00-00 - Y000-00-00\",\n            options: {\n                clearIfNotMatch: false,\n                placeholder: \"YYYY-MM-DD - YYYY-MM-DD\",\n                translation: {\n                    Y: {pattern: /[1-9]/},\n                }\n            }\n        }\n    };\n\n    /**\n     * Toggle display of approximate date placeholders based on checkbox state\n     */\n    function toggleApproxDatePlaceholders() {\n        const isApproximate = $(\"#id_date_is_approximate\").is(\":checked\");\n        if (isApproximate) {\n            approxDatePlaceholders.show();\n        } else {\n            approxDatePlaceholders.hide();\n        }\n    }\n\n    /**\n     * Apply the appropriate date mask based on the current value of the date field.\n     */\n    function applyAppropriateRangeMask() {\n        const value = dateField.val();\n    \n        if (value && value.includes(\" - \")) {\n            // Apply range mask if a dash is detected\n            dateField.mask(masks.dateRange.pattern, masks.dateRange.options);\n        } else {\n            dateField.mask(masks.singleDate.pattern, masks.singleDate.options);\n        }\n    }\n  \n    applyAppropriateRangeMask();\n    toggleApproxDatePlaceholders();\n  \n    // Apply appropriate mask when user types\n    dateField.on(\"keyup\", function(e) {\n        const value = $(this).val();\n    \n        // Check if user has entered a complete single date and is trying to add a space\n        if (value.length === 10 && e.key === \" \") {\n            // Remove the current mask to allow space entry\n            $(this).unmask();\n            // Auto-add date separator\n            $(this).val(value + \" - \");\n            // Apply ranged date mask\n            $(this).mask(masks.dateRange.pattern, masks.dateRange.options);\n        } else if (value.includes(\" - \")) {\n            // If it already contains the range separator, use range mask\n            $(this).mask(masks.dateRange.pattern, masks.dateRange.options);\n        } else {\n            // Otherwise use single date mask\n            $(this).mask(masks.singleDate.pattern, masks.singleDate.options);\n        }\n    });\n\n    $(\"#id_date_is_approximate\").on(\"change\", toggleApproxDatePlaceholders);\n});//# sourceURL=[module]\n//# sourceMappingURL=data:application/json;charset=utf-8;base64,eyJ2ZXJzaW9uIjozLCJmaWxlIjoiLi9hcHAvY2FhaXMvc3RhdGljL2NhYWlzL2pzL2FkbWluL2RhdGVPZk1hdGVyaWFscy5qcyIsIm1hcHBpbmdzIjoiQUFBQTtBQUNBO0FBQ0E7QUFDQTs7QUFFQTs7QUFFQTs7QUFFQTtBQUNBOztBQUVBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0Esd0JBQXdCLGlCQUFpQjtBQUN6QztBQUNBO0FBQ0EsU0FBUztBQUNUO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBLHdCQUF3QixpQkFBaUI7QUFDekM7QUFDQTtBQUNBO0FBQ0E7O0FBRUE7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQSxVQUFVO0FBQ1Y7QUFDQTtBQUNBOztBQUVBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBLFVBQVU7QUFDVjtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBLFVBQVU7QUFDVjtBQUNBO0FBQ0EsVUFBVTtBQUNWO0FBQ0E7QUFDQTtBQUNBLEtBQUs7O0FBRUw7QUFDQSxDQUFDIiwic291cmNlcyI6WyJ3ZWJwYWNrOi8vc2VjdXJlLXJlY29yZC10cmFuc2Zlci8uL2FwcC9jYWFpcy9zdGF0aWMvY2FhaXMvanMvYWRtaW4vZGF0ZU9mTWF0ZXJpYWxzLmpzPzJhMWMiXSwic291cmNlc0NvbnRlbnQiOlsiLyoqXG4gKiBBcHBseSBkYXRlIG1hc2sgdG8gdGhlIGRhdGUgb2YgbWF0ZXJpYWxzIGZpZWxkIHVzaW5nIGpRdWVyeSBNYXNrIHBsdWdpbi5cbiAqIFN1cHBvcnRzIGJvdGggc2luZ2xlIGRhdGUgKFlZWVktTU0tREQpIGFuZCBkYXRlIHJhbmdlIChZWVlZLU1NLUREIC0gWVlZWS1NTS1ERCkgZm9ybWF0cy5cbiAqL1xuXG4vKiBnbG9iYWwgZGphbmdvICovXG5cbmNvbnN0ICQgPSBkamFuZ28ualF1ZXJ5O1xuXG4kKGRvY3VtZW50KS5yZWFkeShmdW5jdGlvbigpIHtcbiAgICBjb25zdCBkYXRlRmllbGQgPSAkKFwiI2lkX2RhdGVfb2ZfbWF0ZXJpYWxzXCIpO1xuXG4gICAgLy8gR2V0IHRoZSBwbGFjZWhvbGRlciBlbGVtZW50cyB1c2VkIHRvIGluZGljYXRlIHRoYXQgdGhlIGRhdGUgaXMgYXBwcm94aW1hdGVcbiAgICBjb25zdCBhcHByb3hEYXRlUGxhY2Vob2xkZXJzID0gJChcIi5hcHByb3gtZGF0ZS13cmFwcGVyXCIpO1xuICBcbiAgICBjb25zdCBtYXNrcyA9IHtcbiAgICAgICAgc2luZ2xlRGF0ZToge1xuICAgICAgICAgICAgcGF0dGVybjogXCJZMDAwLTAwLTAwXCIsXG4gICAgICAgICAgICBvcHRpb25zOiB7XG4gICAgICAgICAgICAgICAgY2xlYXJJZk5vdE1hdGNoOiBmYWxzZSxcbiAgICAgICAgICAgICAgICBwbGFjZWhvbGRlcjogXCJZWVlZLU1NLUREXCIsXG4gICAgICAgICAgICAgICAgdHJhbnNsYXRpb246IHtcbiAgICAgICAgICAgICAgICAgICAgWToge3BhdHRlcm46IC9bMS05XS99LFxuICAgICAgICAgICAgICAgIH1cbiAgICAgICAgICAgIH1cbiAgICAgICAgfSxcbiAgICAgICAgZGF0ZVJhbmdlOiB7XG4gICAgICAgICAgICBwYXR0ZXJuOiBcIlkwMDAtMDAtMDAgLSBZMDAwLTAwLTAwXCIsXG4gICAgICAgICAgICBvcHRpb25zOiB7XG4gICAgICAgICAgICAgICAgY2xlYXJJZk5vdE1hdGNoOiBmYWxzZSxcbiAgICAgICAgICAgICAgICBwbGFjZWhvbGRlcjogXCJZWVlZLU1NLUREIC0gWVlZWS1NTS1ERFwiLFxuICAgICAgICAgICAgICAgIHRyYW5zbGF0aW9uOiB7XG4gICAgICAgICAgICAgICAgICAgIFk6IHtwYXR0ZXJuOiAvWzEtOV0vfSxcbiAgICAgICAgICAgICAgICB9XG4gICAgICAgICAgICB9XG4gICAgICAgIH1cbiAgICB9O1xuXG4gICAgLyoqXG4gICAgICogVG9nZ2xlIGRpc3BsYXkgb2YgYXBwcm94aW1hdGUgZGF0ZSBwbGFjZWhvbGRlcnMgYmFzZWQgb24gY2hlY2tib3ggc3RhdGVcbiAgICAgKi9cbiAgICBmdW5jdGlvbiB0b2dnbGVBcHByb3hEYXRlUGxhY2Vob2xkZXJzKCkge1xuICAgICAgICBjb25zdCBpc0FwcHJveGltYXRlID0gJChcIiNpZF9kYXRlX2lzX2FwcHJveGltYXRlXCIpLmlzKFwiOmNoZWNrZWRcIik7XG4gICAgICAgIGlmIChpc0FwcHJveGltYXRlKSB7XG4gICAgICAgICAgICBhcHByb3hEYXRlUGxhY2Vob2xkZXJzLnNob3coKTtcbiAgICAgICAgfSBlbHNlIHtcbiAgICAgICAgICAgIGFwcHJveERhdGVQbGFjZWhvbGRlcnMuaGlkZSgpO1xuICAgICAgICB9XG4gICAgfVxuXG4gICAgLyoqXG4gICAgICogQXBwbHkgdGhlIGFwcHJvcHJpYXRlIGRhdGUgbWFzayBiYXNlZCBvbiB0aGUgY3VycmVudCB2YWx1ZSBvZiB0aGUgZGF0ZSBmaWVsZC5cbiAgICAgKi9cbiAgICBmdW5jdGlvbiBhcHBseUFwcHJvcHJpYXRlUmFuZ2VNYXNrKCkge1xuICAgICAgICBjb25zdCB2YWx1ZSA9IGRhdGVGaWVsZC52YWwoKTtcbiAgICBcbiAgICAgICAgaWYgKHZhbHVlICYmIHZhbHVlLmluY2x1ZGVzKFwiIC0gXCIpKSB7XG4gICAgICAgICAgICAvLyBBcHBseSByYW5nZSBtYXNrIGlmIGEgZGFzaCBpcyBkZXRlY3RlZFxuICAgICAgICAgICAgZGF0ZUZpZWxkLm1hc2sobWFza3MuZGF0ZVJhbmdlLnBhdHRlcm4sIG1hc2tzLmRhdGVSYW5nZS5vcHRpb25zKTtcbiAgICAgICAgfSBlbHNlIHtcbiAgICAgICAgICAgIGRhdGVGaWVsZC5tYXNrKG1hc2tzLnNpbmdsZURhdGUucGF0dGVybiwgbWFza3Muc2luZ2xlRGF0ZS5vcHRpb25zKTtcbiAgICAgICAgfVxuICAgIH1cbiAgXG4gICAgYXBwbHlBcHByb3ByaWF0ZVJhbmdlTWFzaygpO1xuICAgIHRvZ2dsZUFwcHJveERhdGVQbGFjZWhvbGRlcnMoKTtcbiAgXG4gICAgLy8gQXBwbHkgYXBwcm9wcmlhdGUgbWFzayB3aGVuIHVzZXIgdHlwZXNcbiAgICBkYXRlRmllbGQub24oXCJrZXl1cFwiLCBmdW5jdGlvbihlKSB7XG4gICAgICAgIGNvbnN0IHZhbHVlID0gJCh0aGlzKS52YWwoKTtcbiAgICBcbiAgICAgICAgLy8gQ2hlY2sgaWYgdXNlciBoYXMgZW50ZXJlZCBhIGNvbXBsZXRlIHNpbmdsZSBkYXRlIGFuZCBpcyB0cnlpbmcgdG8gYWRkIGEgc3BhY2VcbiAgICAgICAgaWYgKHZhbHVlLmxlbmd0aCA9PT0gMTAgJiYgZS5rZXkgPT09IFwiIFwiKSB7XG4gICAgICAgICAgICAvLyBSZW1vdmUgdGhlIGN1cnJlbnQgbWFzayB0byBhbGxvdyBzcGFjZSBlbnRyeVxuICAgICAgICAgICAgJCh0aGlzKS51bm1hc2soKTtcbiAgICAgICAgICAgIC8vIEF1dG8tYWRkIGRhdGUgc2VwYXJhdG9yXG4gICAgICAgICAgICAkKHRoaXMpLnZhbCh2YWx1ZSArIFwiIC0gXCIpO1xuICAgICAgICAgICAgLy8gQXBwbHkgcmFuZ2VkIGRhdGUgbWFza1xuICAgICAgICAgICAgJCh0aGlzKS5tYXNrKG1hc2tzLmRhdGVSYW5nZS5wYXR0ZXJuLCBtYXNrcy5kYXRlUmFuZ2Uub3B0aW9ucyk7XG4gICAgICAgIH0gZWxzZSBpZiAodmFsdWUuaW5jbHVkZXMoXCIgLSBcIikpIHtcbiAgICAgICAgICAgIC8vIElmIGl0IGFscmVhZHkgY29udGFpbnMgdGhlIHJhbmdlIHNlcGFyYXRvciwgdXNlIHJhbmdlIG1hc2tcbiAgICAgICAgICAgICQodGhpcykubWFzayhtYXNrcy5kYXRlUmFuZ2UucGF0dGVybiwgbWFza3MuZGF0ZVJhbmdlLm9wdGlvbnMpO1xuICAgICAgICB9IGVsc2Uge1xuICAgICAgICAgICAgLy8gT3RoZXJ3aXNlIHVzZSBzaW5nbGUgZGF0ZSBtYXNrXG4gICAgICAgICAgICAkKHRoaXMpLm1hc2sobWFza3Muc2luZ2xlRGF0ZS5wYXR0ZXJuLCBtYXNrcy5zaW5nbGVEYXRlLm9wdGlvbnMpO1xuICAgICAgICB9XG4gICAgfSk7XG5cbiAgICAkKFwiI2lkX2RhdGVfaXNfYXBwcm94aW1hdGVcIikub24oXCJjaGFuZ2VcIiwgdG9nZ2xlQXBwcm94RGF0ZVBsYWNlaG9sZGVycyk7XG59KTsiXSwibmFtZXMiOltdLCJzb3VyY2VSb290IjoiIn0=\n//# sourceURL=webpack-internal:///./app/caais/static/caais/js/admin/dateOfMaterials.js\n");

/***/ }),

/***/ "./app/caais/static/caais/js/admin/phoneNumberMask.js":
/*!************************************************************!*\
  !*** ./app/caais/static/caais/js/admin/phoneNumberMask.js ***!
  \************************************************************/
/***/ (() => {

eval("/* global django */\n\nwindow.addEventListener(\"load\", function() {\n    (function($) {\n        $(\"input[id$=\\\"-phone_number\\\"\").each(function() {\n            $(this).mask(\"+0 (000) 000-0000\");\n        });\n    })(django.jQuery);\n});\n//# sourceURL=[module]\n//# sourceMappingURL=data:application/json;charset=utf-8;base64,eyJ2ZXJzaW9uIjozLCJmaWxlIjoiLi9hcHAvY2FhaXMvc3RhdGljL2NhYWlzL2pzL2FkbWluL3Bob25lTnVtYmVyTWFzay5qcyIsIm1hcHBpbmdzIjoiQUFBQTs7QUFFQTtBQUNBO0FBQ0E7QUFDQTtBQUNBLFNBQVM7QUFDVCxLQUFLO0FBQ0wsQ0FBQyIsInNvdXJjZXMiOlsid2VicGFjazovL3NlY3VyZS1yZWNvcmQtdHJhbnNmZXIvLi9hcHAvY2FhaXMvc3RhdGljL2NhYWlzL2pzL2FkbWluL3Bob25lTnVtYmVyTWFzay5qcz9lNmQxIl0sInNvdXJjZXNDb250ZW50IjpbIi8qIGdsb2JhbCBkamFuZ28gKi9cblxud2luZG93LmFkZEV2ZW50TGlzdGVuZXIoXCJsb2FkXCIsIGZ1bmN0aW9uKCkge1xuICAgIChmdW5jdGlvbigkKSB7XG4gICAgICAgICQoXCJpbnB1dFtpZCQ9XFxcIi1waG9uZV9udW1iZXJcXFwiXCIpLmVhY2goZnVuY3Rpb24oKSB7XG4gICAgICAgICAgICAkKHRoaXMpLm1hc2soXCIrMCAoMDAwKSAwMDAtMDAwMFwiKTtcbiAgICAgICAgfSk7XG4gICAgfSkoZGphbmdvLmpRdWVyeSk7XG59KTtcbiJdLCJuYW1lcyI6W10sInNvdXJjZVJvb3QiOiIifQ==\n//# sourceURL=webpack-internal:///./app/caais/static/caais/js/admin/phoneNumberMask.js\n");

/***/ }),

/***/ "./app/caais/static/caais/css/base/inlineTextInputs.css":
/*!**************************************************************!*\
  !*** ./app/caais/static/caais/css/base/inlineTextInputs.css ***!
  \**************************************************************/
/***/ ((__unused_webpack_module, __webpack_exports__, __webpack_require__) => {

"use strict";
eval("__webpack_require__.r(__webpack_exports__);\n// extracted by mini-css-extract-plugin\n//# sourceURL=[module]\n//# sourceMappingURL=data:application/json;charset=utf-8;base64,eyJ2ZXJzaW9uIjozLCJmaWxlIjoiLi9hcHAvY2FhaXMvc3RhdGljL2NhYWlzL2Nzcy9iYXNlL2lubGluZVRleHRJbnB1dHMuY3NzIiwibWFwcGluZ3MiOiI7QUFBQSIsInNvdXJjZXMiOlsid2VicGFjazovL3NlY3VyZS1yZWNvcmQtdHJhbnNmZXIvLi9hcHAvY2FhaXMvc3RhdGljL2NhYWlzL2Nzcy9iYXNlL2lubGluZVRleHRJbnB1dHMuY3NzP2FmNjciXSwic291cmNlc0NvbnRlbnQiOlsiLy8gZXh0cmFjdGVkIGJ5IG1pbmktY3NzLWV4dHJhY3QtcGx1Z2luXG5leHBvcnQge307Il0sIm5hbWVzIjpbXSwic291cmNlUm9vdCI6IiJ9\n//# sourceURL=webpack-internal:///./app/caais/static/caais/css/base/inlineTextInputs.css\n");

/***/ }),

/***/ "./app/caais/static/caais/css/base/metadataChangeForm.css":
/*!****************************************************************!*\
  !*** ./app/caais/static/caais/css/base/metadataChangeForm.css ***!
  \****************************************************************/
/***/ ((__unused_webpack_module, __webpack_exports__, __webpack_require__) => {

"use strict";
eval("__webpack_require__.r(__webpack_exports__);\n// extracted by mini-css-extract-plugin\n//# sourceURL=[module]\n//# sourceMappingURL=data:application/json;charset=utf-8;base64,eyJ2ZXJzaW9uIjozLCJmaWxlIjoiLi9hcHAvY2FhaXMvc3RhdGljL2NhYWlzL2Nzcy9iYXNlL21ldGFkYXRhQ2hhbmdlRm9ybS5jc3MiLCJtYXBwaW5ncyI6IjtBQUFBIiwic291cmNlcyI6WyJ3ZWJwYWNrOi8vc2VjdXJlLXJlY29yZC10cmFuc2Zlci8uL2FwcC9jYWFpcy9zdGF0aWMvY2FhaXMvY3NzL2Jhc2UvbWV0YWRhdGFDaGFuZ2VGb3JtLmNzcz9mOWQyIl0sInNvdXJjZXNDb250ZW50IjpbIi8vIGV4dHJhY3RlZCBieSBtaW5pLWNzcy1leHRyYWN0LXBsdWdpblxuZXhwb3J0IHt9OyJdLCJuYW1lcyI6W10sInNvdXJjZVJvb3QiOiIifQ==\n//# sourceURL=webpack-internal:///./app/caais/static/caais/css/base/metadataChangeForm.css\n");

/***/ })

/******/ 	});
/************************************************************************/
/******/ 	// The require scope
/******/ 	var __webpack_require__ = {};
/******/ 	
/************************************************************************/
/******/ 	/* webpack/runtime/make namespace object */
/******/ 	(() => {
/******/ 		// define __esModule on exports
/******/ 		__webpack_require__.r = (exports) => {
/******/ 			if(typeof Symbol !== 'undefined' && Symbol.toStringTag) {
/******/ 				Object.defineProperty(exports, Symbol.toStringTag, { value: 'Module' });
/******/ 			}
/******/ 			Object.defineProperty(exports, '__esModule', { value: true });
/******/ 		};
/******/ 	})();
/******/ 	
/************************************************************************/
/******/ 	
/******/ 	// startup
/******/ 	// Load entry module and return exports
/******/ 	// This entry module can't be inlined because the eval-source-map devtool is used.
/******/ 	__webpack_modules__["./app/caais/static/caais/css/base/metadataChangeForm.css"](0, {}, __webpack_require__);
/******/ 	__webpack_modules__["./app/caais/static/caais/css/base/inlineTextInputs.css"](0, {}, __webpack_require__);
/******/ 	__webpack_modules__["./app/caais/static/caais/js/admin/phoneNumberMask.js"](0, {}, __webpack_require__);
/******/ 	var __webpack_exports__ = {};
/******/ 	__webpack_modules__["./app/caais/static/caais/js/admin/dateOfMaterials.js"](0, __webpack_exports__, __webpack_require__);
/******/ 	
/******/ })()
;