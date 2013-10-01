function resizer(event) {
	var name = event.animationName;
	var banner;

	console.log(name);

	if (name === "big") {
		banner = document.querySelector('.banner');
		if (banner) {
			banner.parentElement.removeChild(banner);
		}
	} else if (name === "small") {
		banner = document.querySelector('.banner');

		if (banner) {
			return;
		}

		banner = document.createElement('div');
		banner.style.position = "fixed";
		banner.style.width = "100%";
		banner.style.height = "100%";
		banner.style.left = "0";
		banner.style.top = "0";
		banner.style.background = "white";
		banner.style.textAlign = "center";
		banner.style.zIndex = "10";
		banner.style.fontSize = "2em";
		banner.className = "banner";

		banner.textContent = "Earth Reader doesn't support small screen.";

		document.body.appendChild(banner);
	}
}

Element.prototype.toggleClass = function(name) {
	if (this.classList.contains(name)) {
		this.classList.remove(name);
	} else {
		this.classList.add(name);
	}
}

function feedListToggle(event) {
	var target = event.target;
	while (target.classList.contains('header') == false) {
		target = target.parentElement;
		if (target === null) {
			return;
		}
	}

	target.toggleClass('closed');
}

function persistentToggle(event) {
	var target = event.target;
	while (target.classList.contains('header') == false) {
		target = target.parentElement;
		if (target === null) {
			return;
		}
	}

	target.toggleClass('opened');
}

function processForm(event) {
	var target = event.target;
	console.log(target);
	event.preventDefault();
}

function init() {
	var persistent = document.querySelector('[role=navigation] .persistent');
	var feedList = document.querySelector('[role=navigation] .feedlist');
	persistent.addEventListener('click', persistentToggle, false);
	feedList.addEventListener('click', feedListToggle, false);

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
