"use strict";


/* --------------------------------------------------------------
   API configuration
   -------------------------------------------------------------- */

const API_BASE = "http://127.0.0.1:8765";

const statusUrl = API_BASE + "/api/status";
const previewUrl = API_BASE + "/api/preview";

const startUrl = API_BASE + "/api/start";
const shutdownUrl = API_BASE + "/api/shutdown";
const resetHDMIUrl = API_BASE + "/api/reset-hdmi";
const fixOpenLPUrl = API_BASE + "/api/fix-openlp";


/* --------------------------------------------------------------
   DOM elements
   -------------------------------------------------------------- */

const statusRows = {
    tv: document.querySelectorAll(".status-row")[0],
    openlp: document.querySelectorAll(".status-row")[1]
};

const feedback = document.querySelector(".feedback");
const lastChecked = document.querySelector(".last-checked");

const startButton = document.getElementById("start-button");
const shutdownButton = document.getElementById("shutdown-button");
const resetHDMIButton = document.getElementById("reset-hdmi-button");
const fixOpenLPButton = document.getElementById("fix-openlp-button");

const previewImage = document.getElementById("tv-preview");
const previewPlaceholder = document.getElementById("preview-placeholder");
const previewUpdated = document.getElementById("preview-updated");


/* --------------------------------------------------------------
   State
   -------------------------------------------------------------- */

let operationInProgress = false;
let haveStatus = false;


/* --------------------------------------------------------------
   Status display
   -------------------------------------------------------------- */

function setStatus(row, text, state) {

    const indicator = row.querySelector(".indicator");
    const label = row.querySelector("span:last-child");

    indicator.classList.remove(
        "checking",
        "ok",
        "error"
    );

    indicator.classList.add(state);

    label.textContent = text;
}


function setFeedback(message) {

    feedback.textContent = message;
}


/* --------------------------------------------------------------
   Update status
   -------------------------------------------------------------- */

function updateStatusDisplay(data) {

    setStatus(
        statusRows.tv,
        "TV Computer: " +
            (data.tv_online ? "OK" : "Not available"),
        data.tv_online ? "ok" : "error"
    );


    setStatus(
        statusRows.openlp,
        "OpenLP Stage View: " +
            (data.openlp_reachable ? "OK" : "Not available"),
        data.openlp_reachable ? "ok" : "error"
    );


    updateActionButtons(data.tv_online);


    lastChecked.textContent =
        "Last checked: " +
        new Date().toLocaleTimeString();


    haveStatus = true;
}


/* --------------------------------------------------------------
   TV buttons
   -------------------------------------------------------------- */

function updateActionButtons(tvOnline) {

    if (operationInProgress) {
        return;
    }


    if (tvOnline) {

        startButton.style.display = "none";
        shutdownButton.style.display = "block";

    } else {

        startButton.style.display = "block";
        shutdownButton.style.display = "none";
    }
}


/* --------------------------------------------------------------
   Enable / disable buttons
   -------------------------------------------------------------- */

function setButtonsEnabled(enabled) {

    startButton.disabled = !enabled;
    shutdownButton.disabled = !enabled;
    resetHDMIButton.disabled = !enabled;
    fixOpenLPButton.disabled = !enabled;
}


/* --------------------------------------------------------------
   TV preview
   -------------------------------------------------------------- */

function hidePreview(message = "Preview unavailable") {

    previewImage.style.display = "none";
    previewImage.removeAttribute("src");

    previewPlaceholder.style.display = "block";
    previewPlaceholder.textContent = message;
}


async function refreshPreview() {

    if (operationInProgress) {
        return;
    }


    try {

        console.log(
            "Fetching TV preview:",
            previewUrl
        );


        const response = await fetch(
            previewUrl + "?t=" + Date.now(),
            {
                cache: "no-store"
            }
        );


        console.log(
            "Preview response:",
            response.status,
            response.statusText,
            response.headers.get("content-type")
        );


        if (!response.ok) {

            throw new Error(
                "HTTP " +
                response.status +
                " " +
                response.statusText
            );
        }


        const blob = await response.blob();


        console.log(
            "Preview received:",
            blob.type,
            blob.size,
            "bytes"
        );


        const objectUrl =
            URL.createObjectURL(blob);


        previewImage.onload = function () {

            previewImage.style.display = "block";
            previewPlaceholder.style.display = "none";


            previewUpdated.textContent =
                "Preview updated: " +
                new Date().toLocaleTimeString();


            URL.revokeObjectURL(objectUrl);
        };


        previewImage.onerror = function () {

            console.error(
                "Preview image failed to load."
            );


            URL.revokeObjectURL(objectUrl);

            hidePreview();
        };


        previewImage.src = objectUrl;


    } catch (error) {

        console.error(
            "TV preview error:",
            error
        );


        hidePreview(
            "Preview unavailable: " +
            error.message
        );
    }
}


/* --------------------------------------------------------------
   Status polling
   -------------------------------------------------------------- */

async function refreshStatus() {

    try {

        const response = await fetch(
            statusUrl,
            {
                cache: "no-store"
            }
        );


        const data = await response.json();


        if (!data.success) {

            throw new Error(
                data.message ||
                "Unable to get status."
            );
        }


        updateStatusDisplay(data);


        if (!operationInProgress) {

            if (data.tv_online) {

                if (data.openlp_reachable) {

                    setFeedback(
                        "TV computer is online."
                    );

                } else {

                    setFeedback(
                        "TV computer is online. " +
                        "Waiting for OpenLP."
                    );
                }

            } else {

                setFeedback(
                    "TV computer is offline. " +
                    "Use Start TV to turn it on."
                );
            }
        }


    } catch (error) {

        console.error(
            "Status error:",
            error
        );


        setStatus(
            statusRows.tv,
            "TV Computer: Not available",
            "error"
        );


        setStatus(
            statusRows.openlp,
            "OpenLP Stage View: Not available",
            "error"
        );


        updateActionButtons(false);


        lastChecked.textContent =
            "Last checked: " +
            new Date().toLocaleTimeString();


        hidePreview(
            "TV preview unavailable"
        );


        if (!operationInProgress) {

            setFeedback(
                "Unable to contact Church TV Control."
            );
        }
    }
}


/* --------------------------------------------------------------
   Generic action
   -------------------------------------------------------------- */

async function performAction(
    url,
    workingMessage,
    successMessage
) {

    operationInProgress = true;

    setButtonsEnabled(false);

    setFeedback(workingMessage);


    try {

        const response = await fetch(
            url,
            {
                method: "POST"
            }
        );


        const data = await response.json();


        if (!data.success) {

            throw new Error(
                data.message ||
                "Operation failed."
            );
        }


        setFeedback(
            data.message ||
            successMessage
        );


    } catch (error) {

        setFeedback(
            "Operation failed: " +
            error.message
        );


    } finally {

        operationInProgress = false;

        setButtonsEnabled(true);


        setTimeout(
            refreshStatus,
            1000
        );


        setTimeout(
            refreshPreview,
            1500
        );
    }
}


/* --------------------------------------------------------------
   Start TV computer
   -------------------------------------------------------------- */

async function startTVComputer() {

    if (operationInProgress) {
        return;
    }


    operationInProgress = true;

    setButtonsEnabled(false);

    startButton.style.display = "block";


    setFeedback(
        "Starting TV computer… Please wait."
    );


    try {

        const response = await fetch(
            startUrl,
            {
                method: "POST"
            }
        );


        const data = await response.json();


        if (!data.success) {

            throw new Error(
                data.message ||
                "Unable to start TV computer."
            );
        }


        await waitForTVComputer();


    } catch (error) {

        console.error(
            "Start TV error:",
            error
        );


        operationInProgress = false;

        setButtonsEnabled(true);

        updateActionButtons(false);


        setFeedback(
            "TV computer did not start: " +
            error.message
        );
    }
}


/* --------------------------------------------------------------
   Wait for TV computer
   -------------------------------------------------------------- */

async function waitForTVComputer() {

    const maximumAttempts = 45;


    for (
        let attempt = 1;
        attempt <= maximumAttempts;
        attempt++
    ) {

        await sleep(2000);


        try {

            const response = await fetch(
                statusUrl,
                {
                    cache: "no-store"
                }
            );


            const data = await response.json();


            if (
                data.success &&
                data.tv_online
            ) {

                updateStatusDisplay(data);


                setFeedback(
                    data.openlp_reachable
                        ? "TV computer is online."
                        : "TV computer is online. Waiting for OpenLP."
                );


                operationInProgress = false;

                setButtonsEnabled(true);

                updateActionButtons(true);


                setTimeout(
                    refreshPreview,
                    1000
                );


                return;
            }


        } catch (error) {

            /*
             * The TV computer is still booting.
             */
        }


        setFeedback(
            "Starting TV computer… " +
            "(" +
            attempt +
            "/" +
            maximumAttempts +
            ")"
        );
    }


    throw new Error(
        "The TV computer did not come online " +
        "within 90 seconds."
    );
}


/* --------------------------------------------------------------
   Sleep
   -------------------------------------------------------------- */

function sleep(milliseconds) {

    return new Promise(
        function (resolve) {

            setTimeout(
                resolve,
                milliseconds
            );
        }
    );
}


/* --------------------------------------------------------------
   Button handlers
   -------------------------------------------------------------- */

startButton.addEventListener(
    "click",
    function () {

        startTVComputer();
    }
);


shutdownButton.addEventListener(
    "click",
    function () {

        const confirmed = window.confirm(
            "Shut down the TV computer?\n\n" +
            "The Church TV display will stop until " +
            "the computer is started again."
        );


        if (!confirmed) {
            return;
        }


        performAction(
            shutdownUrl,
            "Shutting down TV computer…",
            "TV computer is shutting down."
        );
    }
);

resetHDMIButton.addEventListener(
    "click",
    function () {

        const confirmed = window.confirm(
            "Refresh the TV display?\n\n" +
            "The TV screen will briefly go blank while " +
            "the HDMI connection is reset."
        );


        if (!confirmed) {
            return;
        }


        performAction(
            resetHDMIUrl,
            "Refreshing TV display…",
            "TV display has been refreshed."
        );
    }
);

fixOpenLPButton.addEventListener(
    "click",
    function () {

        const confirmed = window.confirm(
            "Fix the OpenLP service problem?\n\n" +
            "This will clear OpenLP's thumbnail cache. " +
            "Your service files and songs will not be deleted."
        );


        if (!confirmed) {
            return;
        }


        performAction(
            fixOpenLPUrl,
            "Fixing OpenLP service problem…",
            "OpenLP service problem has been fixed."
        );
    }
);


/* --------------------------------------------------------------
   Initial status and preview
   -------------------------------------------------------------- */

refreshStatus();
refreshPreview();


/* --------------------------------------------------------------
   Poll status every 10 seconds
   -------------------------------------------------------------- */

setInterval(refreshStatus, 10000);


/* --------------------------------------------------------------
   Refresh preview every 5 seconds
   -------------------------------------------------------------- */

   setInterval(refreshPreview, 5000);