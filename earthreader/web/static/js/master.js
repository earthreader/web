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

function post(url, parameter, onSuccess, onFail) {
	var xhr = new XMLHttpRequest();
	xhr.open('post', url);
	xhr.setRequestHeader("Content-type","application/x-www-form-urlencoded");
	xhr.onreadystatechange = function() {
		if (xhr.readyState !== 4) {
			return;
		}

		if (xhr.status === 200) {
			if (onSuccess instanceof Function) {
				(onSuccess)(xhr.responseText);
			}
		} else {
			if(onFail instanceof Function) {
				(onFail)(xhr);
			}
		}
	}

	xhr.send(parameter);
}

function serializeForm(form) {
	var elements = form.querySelectorAll('input, textarea, select');
	var serialized = [];

	for (var i=0; i<elements.length; i++) {
		if (elements[i].name) {
			var name = encodeURIComponent(elements[i].name);
			var value = encodeURIComponent(elements[i].value);
			serialized.push(name + '=' + value);
		}
	}

	return serialized.join('&');
}

function resizer(event) {
	var name = event.animationName;

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

	closeSide();
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

	closeMenu();
	document.body.toggleClass('side-open');
}

function closeMenu() {
	document.body.removeClass('menu-open');
}

function closeSide() {
	document.body.removeClass('side-open');
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
	event.preventDefault();

	var data = serializeForm(target);
	post(target.action, data, function(res) {
		alert(res);
		target.reset();
	});
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

function getEntries(feed_url, title) {
	var main = document.querySelector('[role=main]');
	main.innerHTML = "";


	//FIXME: use obj.title instead of title argument
	var header = document.createElement('header');
	var h2 = document.createElement('h2');
	header.appendChild(h2);
	h2.textContent = title;

	main.appendChild(header);
	getJSON(feed_url, function(obj) {
		var feed_title = obj.title;
		var entries = obj.entries;

		for (var i=0; i<entries.length; i++) {
			var entry = entries[i];
			var article = document.createElement('article');
			var title = document.createElement('div');

			article.addClass('entry');
			article.setAttribute('data-url', entry.entry_url);
			title.addClass('entry-title');
			title.textContent = entry.title;

			article.appendChild(title);
			main.appendChild(article);
		}
	});
}

function click_feed(event) {
	var target = event.target;

	while (target.classList.contains('feed') === false) {
		target = target.parentElement;
		if (target === null) {
			return;
		}
	}

	var title = target.textContent;
	var url = target.getAttribute('data-url');

	closeMenu();

	getEntries(url, title);
}

function clickEntry(event) {
	var target = event.target;

	while (target.classList.contains('entry') === false) {
		target = target.parentElement;
		if (target === null) {
			return;
		}
	}

	//remove content
	var contents = document.querySelectorAll('.entry-content');
	for (var i=0; i<contents.length; i++) {
		contents[i].parentElement.removeChild(contents[i]);
	}

	var entry_url = target.getAttribute('data-url');
	getJSON(entry_url, function(obj) {
		var content = obj.content;
		var elem = document.createElement('div');
		elem.addClass('entry-content');
		elem.innerHTML = content;
		target.appendChild(elem);
	});
}

function init() {
	var navi = document.querySelector('[role=navigation]');
	navi.addEventListener('click', toggleFolding, false);
	navi.addEventListener('click', click_feed, false);

	var main = document.querySelector('[role=main]');
	main.addEventListener('click', clickEntry, false);

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
