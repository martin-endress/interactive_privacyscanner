function interaction(event, selector) {
    const msg = {'event': event, 'selector': selector};
    console.log('SCANNER_INTERACTION' + JSON.stringify(msg));
}

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

// Event Handlers
function clickHandler(event) {
    try {
        interaction('click', getCssSelector(event.target));
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
