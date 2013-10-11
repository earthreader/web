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
				try {
					var json = JSON.parse(xhr.responseText);
					var error = json.error;
					var message = json.message;
					alert(error + '\n' + message);
				}catch(err) {
					alert(xhr.statusText);
				}
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

function clickPersistentMenu(event) {
	var target = event.target;
	while (target.getAttribute('data-action') == null) {
		target = target.parentElement;
		if (target === null) {
			return;
		}
	}

	var action = target.getAttribute('data-action');
	closeMenu();

	if (action === 'all') {
		getAllEntries();
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

function closeMenu() {
	document.body.removeClass('menu-open');
}

function closeSide() {
	document.body.removeClass('side-open');
}

function processForm(event) {
	var target = event.target;
	event.preventDefault();

	var data = serializeForm(target);
	var after = target.getAttribute('data-after');
	if (after === "makeFeedList") {
		var action = target.action;
		//XXX: data-post or etc
		var current = document.querySelector('[role=navigation] .current');
		var url = current.getAttribute('data-adder');
		if (url) {
			action = url;
		}
		post(action, data, function(res) {
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
	feedList.innerHTML = "";

	var makeCategory = function(parentObj, obj) {
		var header = document.createElement('li');
		var list = document.createElement('li');

		header.addClass('header');
		header.addClass('feed');
		header.setAttribute('role', 'link');
		header.setAttribute('data-entries', obj.entries_url);
		header.setAttribute('data-adder', obj.adder_url);
		header.setAttribute('data-remover', obj.remover_url);
		header.textContent = obj.title;

		list.addClass('fold');

		var ul = document.createElement('ul');
		getJSON(obj.feeds_url, function(obj) {
			for (var i=0; i<obj.categories.length; i++) {
				makeCategory(ul, obj.categories[i]);
			}
			for (var i=0; i<obj.feeds.length; i++) {
				makeFeed(ul, obj.feeds[i]);
			}
		});

		list.appendChild(ul);

		parentObj.appendChild(header);
		parentObj.appendChild(list);
	};

	var makeFeed = function(parentObj, obj) {
		var elem = document.createElement('li');
		elem.addClass('feed');
		elem.setAttribute('data-entries', obj.entries_url);
		elem.setAttribute('data-remover', obj.remover_url);
		elem.setAttribute('role', 'link');
		elem.textContent = obj.title;

		parentObj.appendChild(elem);
	};

	for (var i=0; i<obj.categories.length; i++) {
		makeCategory(feedList, obj.categories[i]);
	}
	for (var i=0; i<obj.feeds.length; i++) {
		makeFeed(feedList, obj.feeds[i]);
	}
}

function refreshFeedList() {
	getJSON('/feeds/', makeFeedList);
}

function getAllEntries() {
	var all_feed = document.querySelector('[role=navigation] [data-action=all]');
	var list = document.querySelectorAll('[role=navigation] .current');
	for (var i=0; i<list.length; i++) {
		list[i].removeClass('current');
	}
	all_feed.addClass('current');
	getEntries('/entries/');
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
			var header = document.createElement('div');
			var time = document.createElement('time');
			var title = document.createElement('span');

			article.addClass('entry');
			article.setAttribute('data-entries', entry.entry_url);
			header.addClass('entry-title');
			header.setAttribute('role', 'button');
			time.textContent = entry.updated;
			title.textContent = entry.title;
			header.appendChild(time);
			header.appendChild(title);

			article.appendChild(header);
			main.appendChild(article);
		}
	});
}

function clickFeed(event) {
	var target = event.target;
	var navi = document.querySelector('[role=navigation]');

	while (target.classList.contains('feed') === false) {
		target = target.parentElement;
		if (target === null) {
			return;
		}
	}

	//set current marker
	var list = navi.querySelectorAll('.current');
	for (var i=0; i<list.length; i++) {
		list[i].removeClass('current');
	}
	target.addClass('current');

	var url = target.getAttribute('data-entries');

	closeMenu();

	getEntries(url);
}

function clickEntry(event) {
	var target = event.target;
	var main = document.querySelector('[role=main]');

	while (target.classList.contains('entry-title') === false) {
		target = target.parentElement;
		if (target === null) {
			return;
		}
	}

	var entry = target.parentElement;
	var entry_url = entry.getAttribute('data-entries');

	getJSON(entry_url, function(obj) {
		//set current marker
		var list = main.querySelectorAll('.current');
		for (var i=0; i<list.length; i++) {
			list[i].removeClass('current');
		}
		target.parentElement.addClass('current');

		//close content
		var content = entry.querySelector('.entry-content');
		if (content) {
			entry.removeChild(content);
			return;
		}

		//remove content
		contents = main.querySelectorAll('.entry-content');
		for (var i=0; i<contents.length; i++) {
			contents[i].parentElement.removeChild(contents[i]);
		}

		var content = obj.content;
		var elem = document.createElement('div');
		elem.addClass('entry-content');
		elem.innerHTML = content;
		entry.appendChild(elem);

		scrollToElement(entry);
	});
}

function keyboardShortcut(event) {
	if (event.target.tagName === 'INPUT' || event.target.tagName === 'TEXTAREA') {
		return;
	}

	var main = document.querySelector('[role=main]');

	switch (event.keyCode) {
		case 74: //j
			var entry = main.querySelector('.current');
			if (entry == null) {
				main.querySelector('.entry').querySelector('.entry-title').click();
				return;
			}
			var next = entry.nextElementSibling;
			if (next == null) {
				return;
			}
			next.querySelector('.entry-title').click();
			break;
		case 75: //k
			var entry = main.querySelector('.current');
			var prev = entry.previousElementSibling;
			if (prev == null) {
				return;
			}
			prev.querySelector('.entry-title').click();
			break;
	}
}

function init() {
	var navi = document.querySelector('[role=navigation]');
	var persistent = navi.querySelector('.persistent');
	navi.addEventListener('click', clickFeed, false);
	persistent.addEventListener('click', clickPersistentMenu, false);
	persistent.addEventListener('click', toggleFolding, false);

	var main = document.querySelector('[role=main]');
	main.addEventListener('click', clickEntry, false);

	document.addEventListener('click', toggleMenu, false);
	document.addEventListener('click', toggleSide, false);

	window.addEventListener('submit', processForm, false);
	window.addEventListener('keydown', keyboardShortcut, false);

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
	getAllEntries();
}

window.addEventListener('DOMContentLoaded', init, false);
