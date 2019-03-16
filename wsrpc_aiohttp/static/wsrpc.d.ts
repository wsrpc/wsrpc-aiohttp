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

        export type eventId = number;
        export type Route = string;

        export interface onEventResult {
            (event: Event): any;
        }

        export interface WSRPCPublic {
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

            call(func: Route, args: Array<any>, params: Object): Promise<any>;
        }

        export interface WSRPC {
            DEBUG: boolean;
            TRACE: boolean;

            new(url: string): WSRPCPublic;
        }
    }
}
