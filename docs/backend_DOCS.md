# SmartZen Backend — Docs & Help Guide

## Overview

SmartZen manages classrooms, labs, and their smart devices (lights, relays,
AC units) across a campus. The backend is a Node/Express API backed by
Postgres (via Prisma) and MQTT for talking to physical devices. Instructors
use it to check into rooms, control devices, and view schedules. Admins use
it to manage users, rooms, and automation rules.

## Authentication & Roles

Every request needs a Bearer access token obtained from `POST /auth/login`.
Tokens are short-lived; use `POST /auth/refresh` with the refresh token to
get a new one without re-entering credentials. There are three roles:

- `admin` — full access, including user management and room provisioning.
- `instructor` — can check into assigned rooms, control devices in an
  active session, and view their own schedule.
- `viewer` — read-only access to dashboards and telemetry.

Role is embedded in the JWT and enforced by middleware on every route.

## Rooms & Devices

Rooms are provisioned by an admin via `POST /rooms`, which generates a
unique QR code tied to that room's id. Each room has one or more devices
(relays) registered under it, identified by an MQTT topic like
`site/{roomId}/{deviceId}/state`. Device state (on/off, online/offline) is
kept in sync in real time over MQTT and pushed to clients over WebSocket.

## Checking Into a Room

Instructors check into a room by scanning the room's QR code with the
SmartZen app. Scanning calls `POST /sessions/checkin` with the room id
encoded in the QR payload. This starts a session: it validates the
instructor is scheduled for that room at the current time, marks the room
as occupied, and unlocks device controls for the duration of the class.
If the QR code doesn't match any room, or the instructor has no schedule
entry for that slot, check-in is rejected with a 403.

Sessions end automatically at the scheduled end time, or early if the
instructor calls `POST /sessions/:id/end`.

## Schedules

Each room has a weekly schedule of class slots (day, start time, end time,
instructor, course). Admins import schedules via CSV upload
(`POST /schedules/import`), which validates against existing slots and
rejects any overlapping bookings for the same room. Conflicting rows are
returned in the response so the admin can fix and re-upload just those
rows.

## Energy & Alarms

Every device reports periodic power-usage telemetry over MQTT, stored in
the `telemetry` table. The energy module aggregates this into hourly and
daily totals per room. Alarm rules can be set per room (e.g. "alert if
power draw exceeds 2kW for more than 5 minutes") — when a rule trips, a
notification is created and pushed to connected dashboards over
WebSocket.

## Automation Rules

Automation rules let admins define simple triggers, like "turn off all
lights in a room 10 minutes after the scheduled session ends" or "turn on
AC 5 minutes before a session starts." Rules are evaluated by a background
worker that polls schedule and device state, and execute by publishing
MQTT commands to the relevant device topic.

## Notifications

Notifications (session started/ended, alarm tripped, device went offline)
are delivered two ways: stored in the `notifications` table for the
in-app notification center, and pushed live to any connected client over
the `/ws/notifications` WebSocket channel.
