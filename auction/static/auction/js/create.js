let childrenFileCounter = 0;
let image = document.getElementById("images");

function getChildElementCount() {
    return image.childElementCount;
}

function createFileElement() {
    let newInput = document.createElement("input");
    newInput.type = "file";
    newInput.name = "file_upload";
    newInput.className = "fileupload";
    return newInput;
}

function createFileInput(childElementCount, e) {
    for (let i = 0; i < childElementCount; i++) {
        if (childrenFileCounter > 3) {
            break;
        } else {
            if (image.children[childrenFileCounter].files.length === 1) {
                childrenFileCounter += 1;
                image.appendChild(createFileElement());
            } 
        }
    }
}

function buildErrorElements(text) {
    let createUl = document.createElement("ul");
    let createLi = document.createElement("li");
    let errorBox = document.getElementById("error-box");
    createUl.className = "messages";
    createLi.className = "warning";
    errorBox.appendChild(createUl);
    createUl.appendChild(createLi);
    createLi.textContent = text;
}

function scrollBackToTop(){
    document.documentElement.scrollTop=0;
}

function raiseErrors() {
    let counter = 0;
    let childElements = getChildElementCount();
    for (let i = 0; i < childElements; i++) {
        if (image.children[i].files.length === 1) {
            counter++;
        }
    }
    if (counter < childElements) {
        buildErrorElements(`You can't add another one until previous has been added!`)
        scrollBackToTop()
    } else if (childElements === 5) {
        buildErrorElements(`You can't add more than 5 pictures!`)
        scrollBackToTop()
    }
    return childElements;
}

function sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}

async function removeError() {
    await sleep(10000);
    document.getElementById("error-box").remove()
}

document.getElementById("add_image").onclick = function(e) {
    raiseErrors()
    if (getChildElementCount() === 0) {
        image.appendChild(createFileElement())
    } 
    createFileInput(getChildElementCount(), e)
    removeError()
}