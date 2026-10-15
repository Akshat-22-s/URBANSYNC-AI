'use client';

import { useEffect, useRef, useState, useCallback } from 'react';
import { useUrbanSyncStore } from '@/store/useUrbanSyncStore';
import type {
  SocketChannel,
  SocketMessage,
  CitizenTelemetryPacket,
  WasteNode,
  GreenWaveCorridor,
  EmergencyEscalationPayload,
  DispatchEvent,
} from '@/types';

export interface UseSocketReturn {
  isConnected: boolean;
  lastMessage: SocketMessage | null;
  sendMessage: (data: string | Record<string, unknown>) => boolean;
}

export function useSocket(channel: SocketChannel): UseSocketReturn {
  const [isConnected, setIsConnected] = useState<boolean>(false);
  const [lastMessage, setLastMessage] = useState<SocketMessage | null>(null);

  const socketRef = useRef<WebSocket | null>(null);
  const reconnectAttemptRef = useRef<number>(0);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const isUnmountedRef = useRef<boolean>(false);

  // Store actions
  const updateCitizen = useUrbanSyncStore((s) => s.updateCitizen);
  const updateWasteBin = useUrbanSyncStore((s) => s.updateWasteBin);
  const setGreenCorridors = useUrbanSyncStore((s) => s.setGreenCorridors);
  const triggerDuress = useUrbanSyncStore((s) => s.triggerDuress);
  const addEvent = useUrbanSyncStore((s) => s.addEvent);
  const setCockpitConnected = useUrbanSyncStore((s) => s.setCockpitConnected);

  const connect = useCallback(() => {
    if (typeof window === 'undefined') return;
    if (isUnmountedRef.current) return;

    // Resolve base WebSocket URL
    const rawUrl = process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:8000';
    const baseUrl = rawUrl.replace(/\/+$/, '');
    const wsUrl = `${baseUrl}/ws/${channel}`;

    try {
      const ws = new WebSocket(wsUrl);
      socketRef.current = ws;

      ws.onopen = () => {
        if (isUnmountedRef.current) {
          ws.close();
          return;
        }
        setIsConnected(true);
        reconnectAttemptRef.current = 0;

        if (channel === 'cockpit') {
          setCockpitConnected(true);
        }
      };

      ws.onmessage = (event: MessageEvent) => {
        if (isUnmountedRef.current) return;

        try {
          const data = JSON.parse(event.data);
          const parsedMessage = data as SocketMessage;
          setLastMessage(parsedMessage);

          // Handle message routing by type
          const msgType = parsedMessage.type;
          const payload = parsedMessage.payload;

          switch (msgType) {
            case 'TELEMETRY_UPDATE': {
              if (payload) {
                updateCitizen(payload as CitizenTelemetryPacket);
              }
              break;
            }

            case 'WASTE_DELTA': {
              if (payload) {
                updateWasteBin(payload as WasteNode);
              }
              break;
            }

            case 'GREEN_CORRIDOR': {
              if (Array.isArray(payload)) {
                setGreenCorridors(payload as GreenWaveCorridor[]);
              } else if (payload) {
                setGreenCorridors([payload as unknown as GreenWaveCorridor]);
              }
              break;
            }

            case 'SAFETY_ALERT': {
              if (payload) {
                const emergencyPayload = payload as EmergencyEscalationPayload;
                if (emergencyPayload.code || emergencyPayload.pin_type) {
                  triggerDuress(emergencyPayload);
                } else {
                  addEvent(payload as DispatchEvent);
                }
              }
              break;
            }

            case 'DISPATCH_EVENT': {
              if (payload) {
                addEvent(payload as DispatchEvent);
              }
              break;
            }

            default: {
              // Check if raw payload has event_type (fallback for direct event streams)
              if (data && typeof data === 'object' && 'event_type' in data) {
                addEvent(data as DispatchEvent);
              }
              break;
            }
          }
        } catch (err) {
          console.error('[UrbanSync Socket] Error parsing WebSocket message:', err);
        }
      };

      ws.onerror = (error) => {
        console.warn(`[UrbanSync Socket] Error on channel ${channel}:`, error);
        ws.close();
      };

      ws.onclose = () => {
        setIsConnected(false);
        if (channel === 'cockpit') {
          setCockpitConnected(false);
        }

        if (!isUnmountedRef.current) {
          // Exponential backoff: 1s, 2s, 4s, 8s (capped at 8000ms)
          const delay = Math.min(
            1000 * Math.pow(2, reconnectAttemptRef.current),
            8000
          );
          reconnectAttemptRef.current += 1;

          reconnectTimeoutRef.current = setTimeout(() => {
            connect();
          }, delay);
        }
      };
    } catch (err) {
      console.error(`[UrbanSync Socket] Connection attempt failed for ${channel}:`, err);
      // Attempt reconnect on failed instantiation
      const delay = Math.min(
        1000 * Math.pow(2, reconnectAttemptRef.current),
        8000
      );
      reconnectAttemptRef.current += 1;
      reconnectTimeoutRef.current = setTimeout(() => {
        connect();
      }, delay);
    }
  }, [channel, updateCitizen, updateWasteBin, setGreenCorridors, triggerDuress, addEvent, setCockpitConnected]);

  useEffect(() => {
    isUnmountedRef.current = false;
    connect();

    return () => {
      isUnmountedRef.current = true;
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
        reconnectTimeoutRef.current = null;
      }
      if (socketRef.current) {
        socketRef.current.close();
        socketRef.current = null;
      }
      setIsConnected(false);
    };
  }, [connect]);

  const sendMessage = useCallback((data: string | Record<string, unknown>): boolean => {
    if (socketRef.current && socketRef.current.readyState === WebSocket.OPEN) {
      const messageStr = typeof data === 'string' ? data : JSON.stringify(data);
      socketRef.current.send(messageStr);
      return true;
    }
    console.warn(`[UrbanSync Socket] Unable to send message. Socket not OPEN for ${channel}`);
    return false;
  }, [channel]);

  return {
    isConnected,
    lastMessage,
    sendMessage,
  };
}
