import obspython as obs
import subprocess


STATUS_URL = "http://127.0.0.1:8765/api/status"
SHUTDOWN_URL = "http://127.0.0.1:8765/api/shutdown"


def script_load(settings):
    print("[Church TV] Shutdown prompt loaded.")


def script_unload():
    print("[Church TV] OBS is closing - checking TV status.")

    command = f'''
        STATUS=$(/usr/bin/curl -s --max-time 5 "{STATUS_URL}")

        if [ -z "$STATUS" ]; then
            echo "[Church TV] Could not contact Church TV Control."
            exit 0
        fi

        if echo "$STATUS" | /usr/bin/grep -q '"tv_online": *true'; then

            if /usr/bin/zenity \
                --question \
                --title="Church TV" \
                --text="Do you want to shut down the Church TV computer?" \
                --ok-label="Shut Down TV" \
                --cancel-label="Leave TV Running" \
                --width=400
            then
                echo "[Church TV] User chose to shut down TV."

                /usr/bin/curl \
                    -s \
                    --max-time 10 \
                    -X POST \
                    "{SHUTDOWN_URL}" \
                    >/dev/null
            else
                echo "[Church TV] User chose to leave TV running."
            fi

        else
            echo "[Church TV] TV computer is already offline."
        fi
    '''

    subprocess.Popen(
        ["/bin/bash", "-c", command],
        start_new_session=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    print("[Church TV] TV status check launched.")


