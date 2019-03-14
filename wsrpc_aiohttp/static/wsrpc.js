(function (global) {
	function WSRPCConstructor (URL, reconnectTimeout) {
		var self = this;
		self.id = 1;
		self.eventId = 0;
		self.socketStarted = false;
		self.eventStore = {
			onconnect: {},
			onerror: {},
			onclose: {},
			onchange: {}
		};
		self.connectionNumber = 0;
		self.oneTimeEventStore = {
			onconnect: [],
			onerror: [],
			onclose: [],
			onchange: []
		};

		self.callQueue = [];

		var log = function (msg) {
			if (global.WSRPC.DEBUG) {
				if ('group' in console && 'groupEnd' in console) {
					console.group('WSRPC.DEBUG');
					console.debug(msg);
					console.groupEnd();
				} else {
					console.debug(msg);
				}
			}
		};

		var trace = function (msg) {
			if (global.WSRPC.TRACE) {
				if ('group' in console && 'groupEnd' in console && 'dir' in console) {
					console.group('WSRPC.TRACE');
					if ('data' in msg) {
						console.dir(JSON.parse(msg.data));
					} else {
						console.dir(msg)
					}
					console.groupEnd();
				} else {
					if ('data' in msg) {
						console.log('OBJECT DUMP: ' + msg.data);
					} else {
						console.log('OBJECT DUMP: ' + msg);
					}
				}
			}
		};

		var readyState = {
			0: 'CONNECTING',
			1: 'OPEN',
			2: 'CLOSING',
			3: 'CLOSED'
		};

		function reconnect(callEvents) {
			setTimeout(function () {
				try {
					self.socket = createSocket();
					self.id = 1;
				} catch (exc) {
					callEvents('onerror', exc);
					delete self.socket;
					log(exc);
				}
			}, reconnectTimeout || 1000);
		}

		function createSocket (ev) {
			var ws = new WebSocket(URL);

			var rejectQueue = function () {
				self.connectionNumber++; // rejects incoming calls

				//reject all pending calls
				while (0 < self.callQueue.length) {
					var callObj = self.callQueue.shift();
					var deferred = self.store[callObj.serial];
					delete self.store[callObj.serial];

					if (deferred && deferred.promise.isPending()) {
						deferred.reject('WebSocket error occurred');
					}
				}

				// reject all from the store
				for (var key in self.store) {
					var deferred = self.store[key];

					if (deferred && deferred.promise.isPending()) {
						deferred.reject('WebSocket error occurred');
					}
				}
			};

			ws.onclose = function (err) {
				log('WSRPC: ONCLOSE CALLED (STATE: ' + self.public.state() + ')');
				trace(err);

				for (var serial in self.store) {
					if (self.store[serial].hasOwnProperty('reject') && self.store[serial].promise.isPending()) {
						self.store[serial].reject('Connection closed');
					}
				}

				rejectQueue();
				callEvents('onclose', ev);
				callEvents('onchange', ev);
				reconnect(callEvents);
			};

			ws.onerror = function (err) {
				log('WSRPC: ONERROR CALLED (STATE: ' + self.public.state() + ')');
				trace(err);

				rejectQueue();
				callEvents('onerror', err);
				callEvents('onchange', err);

				log(['WebSocket has been closed by error: ', err]);
			};

			function tryCallEvent(func, event) {
				try {
					return func(event);
				} catch (e) {
					if (e.hasOwnProperty('stack')) {
						log(e.stack);
					} else {
						log('Event function ' + func + ' raised unknown error: ' + e);
					}
				}
			}

			function callEvents(evName, event) {
				while (0 < self.oneTimeEventStore[evName].length) {
					var def = self.oneTimeEventStore[evName].shift();
					// TODO: проверить deferred ли это и state === pending
					if (def.hasOwnProperty('resolve') && def.promise.isPending()) {
						def.resolve();
					}
				}

				for (var i in self.eventStore[evName]) {
					var cur = self.eventStore[evName][i];
					tryCallEvent(cur, event);
				}
			}

			ws.onopen = function (ev) {
				log('WSRPC: ONOPEN CALLED (STATE: ' + self.public.state() + ')');
				trace(ev);

				while (0 < self.callQueue.length) {
					self.socket.send(JSON.stringify(self.callQueue.shift(), 0, 1));
				}

				callEvents('onconnect', ev);
				callEvents('onchange', ev);
			};

			ws.onmessage = function (message) {
				log('WSRPC: ONMESSAGE CALLED (' + self.public.state() + ')');
				trace(message);
				var data = null;
				if (message.type == 'message') {
					try {
						data = JSON.parse(message.data);
						log(data.data);
						if (data.hasOwnProperty('method')) {
							if (!self.routes.hasOwnProperty(data.method)) {
								throw Error('Route not found');
							}

							var connectionNumber = self.connectionNumber;
							Q(self.routes[data.method](data.params)).then(function(promisedResult) {
								if (connectionNumber == self.connectionNumber) {
									self.socket.send(JSON.stringify({
										id: data.id,
										result: promisedResult,
										error: null
									}));
								}
							}).done();
						} else if (data.hasOwnProperty('error') && data.error === null) {
							if (!self.store.hasOwnProperty(data.id)) {
								return log('Unknown callback');
							}
							var deferred = self.store[data.id];
							if (typeof deferred === 'undefined') {
								return log('Confirmation without handler');
							}
							delete self.store[data.id];
							log('REJECTING: ' + data.error);
							deferred.reject(data.error);
						} else {
							var deferred = self.store[data.id];
							if (typeof deferred === 'undefined') {
								return log('Confirmation without handler');
							}
							delete self.store[data.id];
							if (data.result) {
								return deferred.resolve(data.result);
							} else {
								return deferred.reject(data.error);
							}
						}
					} catch (exception) {
						var err = {
							error: exception.message,
							result: null,
							id: data?data.id:null
						};

						self.socket.send(JSON.stringify(err));
						log(exception.stack);
					}
				}
			};

			return ws;
		}

		var makeCall = function (func, args, params) {
			self.id += 2;
			var deferred = Q.defer();

			var callObj = {
				id: self.id,
				method: func,
				// type: 'callback', // By default.
				params: args
			};

			var state = self.public.state();

			if (state === 'OPEN') {
				self.store[self.id] = deferred;
				self.socket.send(JSON.stringify(callObj));
			} else if (state === 'CONNECTING') {
				log('SOCKET IS: ' + state);
				self.store[self.id] = deferred;
				self.callQueue.push(callObj);
			} else {
				log('SOCKET IS: ' + state);
				if (params && params.noWait) {
					deferred.reject('Socket is: ' + state);
				} else {
					self.store[self.id] = deferred;
					self.callQueue.push(callObj);
				}
			}

			return deferred.promise;
		};

		self.routes = {};
		self.store = {};
		self.public = {
			call: function (func, args, params) {
				return makeCall(func, args, params);
			},
			init: function () {
				log('Websocket initializing..')
			},
			addRoute: function (route, callback) {
				self.routes[route] = callback;
			},
			addEventListener: function (event, func, returnId) {
				if (returnId === undefined) {
					returnId = false;
				}

				var eventId = self.eventId++;

				self.eventStore[event][eventId] = func;

				if (returnId) {
					return eventId;
				} else {
					return func;
				}
			},
			onEvent: function (event) {
				var deferred = Q.defer();
				self.oneTimeEventStore[event].push(deferred);
				return deferred.promise;
			},
			removeEventListener: function (event, index) {
				if (self.eventStore[event].hasOwnProperty(index)) {
					delete self.eventStore[event][index];
					return true;
				} else {
					return false;
				}
			},
			deleteRoute: function (route) {
				return delete self.routes[route];
			},
			destroy: function () {
				function placebo () {}
				self.socket.onclose = placebo;
				self.socket.onerror = placebo;
				return self.socket.close();
			},
			state: function () {
				if (self.socketStarted && self.socket) {
					return readyState[self.socket.readyState];
				} else {
					return readyState[3];
				}
			},
			connect: function () {
				self.socketStarted = true;
				self.socket = createSocket();
			}
		};

		self.public.addRoute('log', function (argsObj) {
			console.info('Websocket sent: ' + argsObj);
		});

		self.public.addRoute('ping', function (data) {
			return data;
		});

		return self.public;
	}

	global.WSRPC = WSRPCConstructor;
	global.WSRPC.DEBUG = false;
	global.WSRPC.TRACE = false;
})(this);
