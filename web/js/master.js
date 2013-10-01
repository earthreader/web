Element.prototype.toggleClass = function(name) {
	if (this.classList.contains(name)) {
		this.classList.remove(name);
	} else {
		this.classList.add(name);
	}
};

Element.prototype.removeClass = function(name) {
	if (this.classList.contains(name)) {
		this.classList.remove(name);
	}
};

Element.prototype.addClass = function(name) {
	if (this.classList.contains(name) === false) {
		this.classList.add(name);
	}
}

function resizer(event) {
	var name = event.animationName;

	console.log(name);

	if (name === "big") {
		document.body.removeClass('menu-open');
	} else if (name === "small") {
	}
}

function toggleMenu(event) {
	var target = event.target;
	while (target.classList.contains('off-canvas-menu') == false) {
		target = target.parentElement;
		if (target === null) {
			return;
		}
	}

	document.body.toggleClass('menu-open');
}

function toggleFolding(event) {
	var target = event.target;
	while (target.classList.contains('header') == false) {
		target = target.parentElement;
		if (target === null) {
			return;
		}
	}

	target.toggleClass('closed');
}

function processForm(event) {
	var target = event.target;
	console.log(target);
	event.preventDefault();
}

function init() {
	var navi = document.querySelector('[role=navigation]');
	navi.addEventListener('click', toggleFolding, false);

	document.addEventListener('click', toggleMenu, false);

	window.addEventListener('submit', processForm, false);

    var animationEnd;
    if (document.body.style.animation !== undefined) {
        animationEnd = 'animationend';
    } else if (document.body.style.MozAnimation !== undefined) {
        animationEnd = 'animaionend';
    } else if (document.body.style.webkitAnimation !== undefined) {
        animationEnd = 'webkitAnimationEnd';
    } else if (document.body.style.OAnimtion !== undefined) {
        animationEnd = 'oAnimationEnd';
    } else if (document.body.style.msAnimation !== undefined) {
        animationEnd = 'MSAnimaionEnd';
    }
    document.body.addEventListener(animationEnd, resizer, false);
}

window.addEventListener('DOMContentLoaded', init, false);
