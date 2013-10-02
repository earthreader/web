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

function getJSON(url, onSuccess, onFail) {
	var xhr = new XMLHttpRequest();
	xhr.open('get', url);
	xhr.onreadystatechange = function() {
		if (xhr.readyState !== 4) {
			return;
		}

		if (xhr.status === 200) {
			if (onSuccess instanceof Function) {
				var obj = JSON.parse(xhr.responseText);
				(onSuccess)(obj);
			}
		} else {
			if(onFail instanceof Function) {
				(onFail)(xhr);
			}
		}
	}
	xhr.send();
}

function resizer(event) {
	var name = event.animationName;

	console.log(name);

	if (name === "big") {
		document.body.removeClass('menu-open');
	} else if (name === "small") {
		document.body.removeClass('menu-open');
		document.body.removeClass('side-open');
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

	document.body.removeClass('side-open');
	document.body.toggleClass('menu-open');
}

function toggleSide(event) {
	var target = event.target;
	while (target.classList.contains('off-canvas-side') == false) {
		target = target.parentElement;
		if (target === null) {
			return;
		}
	}

	document.body.removeClass('menu-open');
	document.body.toggleClass('side-open');
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

function refreshFeedList() {
	var feedList = document.querySelector('.feedlist');

	getJSON('/feeds/', function(obj) {
		var feeds = obj.feeds;
		feedList.innerHTML = "";

		for (var i=0; i<feeds.length; i++) {
			var feed = feeds[i];
			var elem = document.createElement('li');
			elem.addClass('feed');
			elem.setAttribute('data-url', feed.feed_url);
			elem.textContent = feed.title;
			feedList.appendChild(elem);
		}
	});
}

function init() {
	var navi = document.querySelector('[role=navigation]');
	navi.addEventListener('click', toggleFolding, false);

	document.addEventListener('click', toggleMenu, false);
	document.addEventListener('click', toggleSide, false);

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

	refreshFeedList();
}

window.addEventListener('DOMContentLoaded', init, false);
