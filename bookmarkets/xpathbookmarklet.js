/**
 * Gets an XPath for an element which describes its hierarchical location.
 */
var getElementXPath = function(element)
{
    if (element && element.id)
        return '//*[@id="' + element.id + '"]';
    else
        return getElementTreeXPath(element);
};

var getElementTreeXPath = function(element)
{
    var paths = [];

    // Use nodeName (instead of localName) so namespace prefix is included (if any).
    for (; element && element.nodeType == 1; element = element.parentNode)
    {
        var index = 0;
        for (var sibling = element.previousSibling; sibling; sibling = sibling.previousSibling)
        {
            // Ignore document type declaration.
            if (sibling.nodeType == Node.DOCUMENT_TYPE_NODE)
                continue;

            if (sibling.nodeName == element.nodeName)
                ++index;
        }

        var tagName = element.nodeName.toLowerCase();
        var pathIndex = (index ? "[" + (index+1) + "]" : "");
        paths.splice(0, 0, tagName + pathIndex);
    }

    return paths.length ? "/" + paths.join("/") : null;
};

function onmouseover (event) 
{
   event.target.setAttribute("style", "outline: 2px solid blue;");
}

function onmouseout (event) 
{  
   event.target.setAttribute("style", "");
}

function onclick (event) 
{  
   event.preventDefault();
   alert('embed:' + document.location + '||xpath:' + getElementXPath(event.target));
}

var item = document.getElementsByTagName("body")[0];

item.addEventListener("mouseover", onmouseover, false);
item.addEventListener("mouseout", onmouseout, false);
item.addEventListener("click", onclick, false);
