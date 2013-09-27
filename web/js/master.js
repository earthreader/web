function resizer(event) {
	var name = event.animationName;
	var banner;

	console.log(name);

	if (name === "big") {
		banner = document.querySelector('.banner');
		banner.parentElement.removeChild(banner);
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

function folderToggle(event) {
	var target = event.target;
	while (target.nodeName !== 'HEADER') {
		target = target.parentElement;
		if (target === null) {
			return;
		}
	}

	if (target.classList.contains('closed')) {
		target.classList.remove('closed');
	} else {
		target.classList.add('closed');
	}
}

function init() {
	var navi = document.querySelector('[role=navigation]');
	navi.addEventListener('click', folderToggle, false);

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
