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

function scrollToElement(element) {
	var x = 0;
    var y = 0;
    while( element && !isNaN( element.offsetLeft ) && !isNaN( element.offsetTop ) ) {
        x += element.offsetLeft - element.scrollLeft;
        y += element.offsetTop - element.scrollTop;
        element = element.offsetParent;
    }

	window.scrollTo(x, y);
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
			} else {
				alert(xhr.statusText);
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
				var obj = JSON.parse(xhr.responseText);
				(onSuccess)(obj);
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
	var after = target.getAttribute('data-after');
	if (after === "makeFeedList") {
		post(target.action, data, function(res) {
			makeFeedList(res);
			target.reset();
		});
	} else {
		post(target.action, data, function(res) {
			alert(res);
			target.reset();
		});
	}
}

function makeFeedList(obj) {
	var feedList = document.querySelector('.feedlist');
	var feeds = obj.feeds;
	feedList.innerHTML = "";

	var makeCategory = function(parentObj, obj) {
		var header = document.createElement('li');
		var list = document.createElement('li');

		header.addClass('header');
		header.textContent = obj.title;

		list.addClass('fold');

		var ul = document.createElement('ul');
		for (var i=0; i<obj.feeds.length; i++) {
			var feed = obj.feeds[i];
			if (feed.feeds) {
				makeCategory(ul, feed);
			} else {
				makeFeed(ul, feed);
			}
		}

		list.appendChild(ul);

		parentObj.appendChild(header);
		parentObj.appendChild(list);
	};

	var makeFeed = function(parentObj, obj) {
		var elem = document.createElement('li');
		elem.addClass('feed');
		elem.setAttribute('data-url', obj.feed_url);
		elem.textContent = obj.title;

		parentObj.appendChild(elem);
	};

	for (var i=0; i<feeds.length; i++) {
		var feed = feeds[i];
		if (feed.feeds) {
			makeCategory(feedList, feed);
		} else {
			makeFeed(feedList, feed);
		}
	}

	list.appendChild(ul);

	parentObj.appendChild(header);
	parentObj.appendChild(list);
}

function refreshFeedList() {
	getJSON('/feeds/', makeFeedList);
}

function getEntries(feed_url) {
	var main = document.querySelector('[role=main]');
	main.innerHTML = "";


	getJSON(feed_url, function(obj) {
		var feed_title = obj.title;
		var entries = obj.entries;

		var header = document.createElement('header');
		var h2 = document.createElement('h2');
		header.appendChild(h2);
		h2.textContent = feed_title;

		main.appendChild(header);

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

	var url = target.getAttribute('data-url');

	closeMenu();

	getEntries(url);
}

function clickEntry(event) {
	var target = event.target;

	while (target.classList.contains('entry-title') === false) {
		target = target.parentElement;
		if (target === null) {
			return;
		}
	}

	var entry = target.parentElement;

	//close content
	var content = entry.querySelector('.entry-content');
	if (content) {
		entry.removeChild(content);
		return;
	}

	//remove content
	contents = document.querySelectorAll('.entry-content');
	for (var i=0; i<contents.length; i++) {
		contents[i].parentElement.removeChild(contents[i]);
	}

	var entry_url = entry.getAttribute('data-url');
	getJSON(entry_url, function(obj) {
		var content = obj.content;
		var elem = document.createElement('div');
		elem.addClass('entry-content');
		elem.innerHTML = content;
		entry.appendChild(elem);

		scrollToElement(entry);
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
