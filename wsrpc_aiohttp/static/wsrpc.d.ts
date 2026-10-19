export namespace NWsRPC {
    export module Main {
        export enum States {
            CONNECTING = 'CONNECTING',
            OPEN = 'OPEN',
            CLOSING = 'CLOSING',
            CLOSED = 'CLOSED',
        }

        export enum StateCodes {
            CONNECTING = 0,
            OPEN = 1,
            CLOSING = 2,
            CLOSED = 3,
        }

        export enum Events {
            onconnect = 'onconnect',
            onerror = 'onerror',
            onclose = 'onclose',
            onchange = 'onchange',
        }


        export interface Deferred {
            resolve(result: any): any;
            reject(error: any): any;
            done: boolean;
            promise: Promise<any>;
        }

        export type eventId = number;
        export type Route = string;
        export interface CallInterface {
            (func: Route, args: Array<any>, params: Object): Promise<any>
        }
        export interface ProxyInterface extends Record<string, CallInterface | ProxyInterface> {}

        export interface onEventResult {
            (event: Event): any;
        }

        export interface WSRPCPublic {
            defer(): Deferred;
            connect(): void;
            destroy(): void;

            state(): States;
            stateCode(): StateCodes;

            addEventListener(
                event: Events,
                callback: (event: Events) => void
            ): eventId;
            removeEventListener(event: Events, index: eventId): boolean;
            onEvent(): Promise<onEventResult>;

            addRoute(
                route: Route,
                callback: (
                    this: Promise<any>,
                    arguments: any
                ) => boolean,
                isAsync?: boolean | undefined
            ): void;
            deleteRoute(name: Route): void;

            call: CallInterface;
            proxy: ProxyInterface;
            addServerEventListener(
                func: (this: WSRPCPublic, event: object) => any
            ): number;
            removeServerEventListener(index: number): number;
            sendRaw(data: any): any;
        }

        export interface WSRPC {
            DEBUG: boolean;
            TRACE: boolean;

            new(url: string): WSRPCPublic;
        }
    }
}
