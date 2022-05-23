//console.log('a')
//import {RobulaPlus} from 'https://cdn.jsdelivr.net/gh/martin-endress/interactive_privacyscanner@record-interaction/manager/tmp/index.min.js';
//console.log('b')

function sendMsg(msg) {
    console.log('SCANNER' + msg);
}

function interaction(event, selector) {
    sendMsg(selector);
}

// const ROBULA = new RobulaPlus();

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
    interaction('', getCssSelector(event.target));
    //sendMsg(ROBULA.getRobustXPath(event.target, document));
}

// Register Event Handler
if (typeof eventhandler_initialized == "undefined" || !eventhandler_initialized) {
    document.addEventListener('click', clickHandler);

    var eventhandler_initialized = true;
}
