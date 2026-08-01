# SmartZen Frontend — Docs & Help Guide

## Overview

The SmartZen frontend is a React/Vite dashboard used by admins and
instructors, plus a lightweight instructor PWA for in-classroom use. It
talks to the backend API for data and a WebSocket connection for live
updates (device state, alarms, notifications).

## Signing In

Sign in from the login page with your email and password. The access
token is kept in memory only (not localStorage) and is refreshed
automatically in the background before it expires. If your session
expires while the tab is open, you'll be redirected back to login and
returned to the same page after re-authenticating.

## Dashboard & Sessions

The Dashboard Sessions page shows every room's current status: occupied
or free, which instructor is checked in, and a live status dot (green =
online, grey = offline, red = alarm). Clicking a room opens its session
detail, showing connected devices and their current power draw.

## Instructor Schedule & Check-In

Instructors have a dedicated schedule page listing their upcoming
classes. On the day of class, a "Check In" button appears once the class
window opens; tapping it opens the device camera to scan the room's QR
code. A successful scan starts the session and takes the instructor to
the Instructor Session page, where they can toggle lights and AC for
that room.

## Users & Rooms (Admin)

Admins manage accounts and rooms from the Users & Rooms page. Adding a
room generates its QR code, shown on-screen and downloadable as a PNG
for printing and posting outside the physical room. Editing a user lets
an admin change their role (admin/instructor/viewer) or deactivate their
account.

## Schedules Page

Admins view and edit the full weekly schedule grid here, room by room.
Uploading a CSV shows a preview with any conflicting rows highlighted in
red before committing the import, so bad rows can be fixed without
re-uploading the whole file.

## Alarms & Automation

This page lists active alarm rules per room and lets admins create new
ones (metric, threshold, duration). It also shows configured automation
rules (like auto-off after session end) with a toggle to enable/disable
each one without deleting it.

## Energy & Telemetry

Shows power-usage charts per room over selectable time ranges (day,
week, month), plus a live relay grid showing each device's current
on/off state updating in real time over WebSocket.

## Notifications

A bell icon in the top nav shows unread notification count. Opening it
lists recent events (session started/ended, alarm tripped, device
offline) with the oldest marked read once viewed. Notifications also
arrive as toast pop-ups while the app is open.

## Assistant

A chat panel where instructors and admins can ask natural-language
questions, like "how do I check into a room?" or "what's my schedule
tomorrow?" The assistant can answer how-to questions from the docs and,
for account-specific questions, look up the user's actual rooms,
schedule, and sessions.
