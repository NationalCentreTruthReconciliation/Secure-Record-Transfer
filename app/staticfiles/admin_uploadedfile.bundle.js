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

/***/ "./app/recordtransfer/static/recordtransfer/js/admin/hideMediaLink.js":
/*!****************************************************************************!*\
  !*** ./app/recordtransfer/static/recordtransfer/js/admin/hideMediaLink.js ***!
  \****************************************************************************/
/***/ (() => {

eval("document.addEventListener(\"DOMContentLoaded\", () => {\n    // Replace links for media URLs to prevent downloading files\n    document.querySelectorAll(\"a\").forEach((link) => {\n        const href = link.getAttribute(\"href\");\n        if (href.includes(\"media/\")) {\n            link.setAttribute(\"href\", \"#\");\n            link.addEventListener(\"click\", (e) => {\n                e.preventDefault();\n                alert(\"Files can only be downloaded by creating a BagIt Bag for a submission\");\n            });\n        }\n    });\n});\n//# sourceURL=[module]\n//# sourceMappingURL=data:application/json;charset=utf-8;base64,eyJ2ZXJzaW9uIjozLCJmaWxlIjoiLi9hcHAvcmVjb3JkdHJhbnNmZXIvc3RhdGljL3JlY29yZHRyYW5zZmVyL2pzL2FkbWluL2hpZGVNZWRpYUxpbmsuanMiLCJtYXBwaW5ncyI6IkFBQUE7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0EsYUFBYTtBQUNiO0FBQ0EsS0FBSztBQUNMLENBQUMiLCJzb3VyY2VzIjpbIndlYnBhY2s6Ly9zZWN1cmUtcmVjb3JkLXRyYW5zZmVyLy4vYXBwL3JlY29yZHRyYW5zZmVyL3N0YXRpYy9yZWNvcmR0cmFuc2Zlci9qcy9hZG1pbi9oaWRlTWVkaWFMaW5rLmpzP2Q2MzciXSwic291cmNlc0NvbnRlbnQiOlsiZG9jdW1lbnQuYWRkRXZlbnRMaXN0ZW5lcihcIkRPTUNvbnRlbnRMb2FkZWRcIiwgKCkgPT4ge1xuICAgIC8vIFJlcGxhY2UgbGlua3MgZm9yIG1lZGlhIFVSTHMgdG8gcHJldmVudCBkb3dubG9hZGluZyBmaWxlc1xuICAgIGRvY3VtZW50LnF1ZXJ5U2VsZWN0b3JBbGwoXCJhXCIpLmZvckVhY2goKGxpbmspID0+IHtcbiAgICAgICAgY29uc3QgaHJlZiA9IGxpbmsuZ2V0QXR0cmlidXRlKFwiaHJlZlwiKTtcbiAgICAgICAgaWYgKGhyZWYuaW5jbHVkZXMoXCJtZWRpYS9cIikpIHtcbiAgICAgICAgICAgIGxpbmsuc2V0QXR0cmlidXRlKFwiaHJlZlwiLCBcIiNcIik7XG4gICAgICAgICAgICBsaW5rLmFkZEV2ZW50TGlzdGVuZXIoXCJjbGlja1wiLCAoZSkgPT4ge1xuICAgICAgICAgICAgICAgIGUucHJldmVudERlZmF1bHQoKTtcbiAgICAgICAgICAgICAgICBhbGVydChcIkZpbGVzIGNhbiBvbmx5IGJlIGRvd25sb2FkZWQgYnkgY3JlYXRpbmcgYSBCYWdJdCBCYWcgZm9yIGEgc3VibWlzc2lvblwiKTtcbiAgICAgICAgICAgIH0pO1xuICAgICAgICB9XG4gICAgfSk7XG59KTtcbiJdLCJuYW1lcyI6W10sInNvdXJjZVJvb3QiOiIifQ==\n//# sourceURL=webpack-internal:///./app/recordtransfer/static/recordtransfer/js/admin/hideMediaLink.js\n");

/***/ })

/******/ 	});
/************************************************************************/
/******/ 	
/******/ 	// startup
/******/ 	// Load entry module and return exports
/******/ 	// This entry module can't be inlined because the eval-source-map devtool is used.
/******/ 	var __webpack_exports__ = {};
/******/ 	__webpack_modules__["./app/recordtransfer/static/recordtransfer/js/admin/hideMediaLink.js"]();
/******/ 	
/******/ })()
;