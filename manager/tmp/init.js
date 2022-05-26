"use strict";

// apparently required for robula source

exports.__esModule = true;

var robula;

// add requirejs tag to load requirejs (hideous i know)
const script = document.createElement('script');
script.type = 'text/javascript';
script.src = 'https://requirejs.org/docs/release/2.3.5/minified/require.js';

document.head.appendChild(script);

function loadRobula() {
    requirejs(["https://cdn.jsdelivr.net/npm/px-robula-plus@1.0.1/lib/index.min.js"], function () {
        robula = new RobulaPlus();
    });
}

function interaction(event, selector) {
    const msg = {'event': event, 'selector': selector};
    console.log('SCANNER_INTERACTION' + JSON.stringify(msg));
}

function log(msg) {
    // log to elm frontend
    console.log(msg);
}

// Load robula once requirejs is loaded
setTimeout(() => {
    // TODO FIX THIS HIDEOUS HACK ASAP
    loadRobula();
}, 300);


/*
CSS Selector
Source: https://stackoverflow.com/questions/8588301/how-to-generate-unique-css-selector-for-dom-element
 */
function getCssSelector(el) {
    let path = [], parent;
    while (parent = el.parentNode) {
        let tag = el.tagName, siblings;
        path.unshift(el.id ? `#${el.id}` : (siblings = parent.children, [].filter.call(siblings, sibling => sibling.tagName === tag).length === 1 ? tag : `${tag}:nth-child(${1 + [].indexOf.call(siblings, el)})`));
        el = parent;
    }
    return `${path.join(' > ')}`.toLowerCase();
}

/*
Get Robula Plus Selector
Source: https://tsigalko18.github.io/assets/pdf/2015-Leotta-ICST.pdf
and https://github.com/cyluxx/robula-plus/blob/master/README.md
 */
function getRobulaSelector(el) {
    return robula.getRobustXPath(el, document);

}

function isInShadow(el) {
    while (parent = el.parentNode) {
        if (el.toString() === "[object ShadowRoot]") {
            return true;
        }
        el = parent;
    }
    return false;
}

// Event Handlers
function clickHandler(event) {
    try {
        interaction('click', getRobulaSelector(event.target));
    } catch (error) {
        console.log(error);
        // ignore for now
    }
}

// Register Event Handler
if (typeof eventhandler_initialized == "undefined" || !eventhandler_initialized) {
    document.addEventListener('click', clickHandler);
    console.log('Event Listener registered.')
    var eventhandler_initialized = true;
}
