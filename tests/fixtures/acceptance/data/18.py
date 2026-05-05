// SPDX-License-Identifier: GPL-3.0-OR-LATER
// Copyright (c) 2024 Richard Stallman

function start() {
    console.log("Starting...");
}

function process(data) {
    return data.map(x => x * 2);
}

function end() {
    console.log("Done.");
}
