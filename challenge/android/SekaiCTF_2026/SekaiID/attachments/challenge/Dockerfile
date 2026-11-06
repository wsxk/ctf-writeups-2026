# Android AVD emulator for CTF challenges
# Headless x86_64 emulator exposing ADB over the network.
#
# Build:  docker build -t ctf-android .
# Run:    docker run --rm -it --device /dev/kvm -p 5555:5555 ctf-android
#         (then on your machine:  adb connect <host>:5555)
FROM ubuntu:22.04

ARG DEBIAN_FRONTEND=noninteractive

# ---- Configurable build args -------------------------------------------------
# API level / image flavour for the AVD. default|google_apis, x86_64 for KVM.
ARG ANDROID_API=36
ARG ANDROID_IMAGE_TYPE=default
ARG ANDROID_ABI=x86_64
ARG SYSTEM_IMAGE="system-images;android-${ANDROID_API};${ANDROID_IMAGE_TYPE};${ANDROID_ABI}"
# Pinned Google command-line tools (update the number for newer releases).
ARG CMDLINE_TOOLS_VERSION=11076708

# ---- Environment -------------------------------------------------------------
ENV ANDROID_SDK_ROOT=/opt/android-sdk \
    ANDROID_HOME=/opt/android-sdk \
    ANDROID_AVD_HOME=/root/.android/avd \
    AVD_NAME=ctf
ENV PATH="${PATH}:${ANDROID_SDK_ROOT}/cmdline-tools/latest/bin:${ANDROID_SDK_ROOT}/platform-tools:${ANDROID_SDK_ROOT}/emulator"

# ---- OS + emulator runtime dependencies -------------------------------------
RUN apt-get update && apt-get install -y --no-install-recommends \
        ca-certificates \
        curl \
        unzip \
        socat \
        openjdk-17-jdk-headless \
        # headless emulator (swiftshader software GL) runtime libs
        libpulse0 \
        libnss3 \
        libxcomposite1 \
        libxcursor1 \
        libxi6 \
        libxtst6 \
        libxdamage1 \
        libxfixes3 \
        libxrandr2 \
        libgl1 \
        libglu1-mesa \
        libasound2 \
        libxshmfence1 \
    && rm -rf /var/lib/apt/lists/*

# ---- Android SDK command-line tools -----------------------------------------
RUN mkdir -p "${ANDROID_SDK_ROOT}/cmdline-tools" \
    && curl -fsSL -o /tmp/cmdline-tools.zip \
        "https://dl.google.com/android/repository/commandlinetools-linux-${CMDLINE_TOOLS_VERSION}_latest.zip" \
    && unzip -q /tmp/cmdline-tools.zip -d /tmp/cmdline-tools \
    && mv /tmp/cmdline-tools/cmdline-tools "${ANDROID_SDK_ROOT}/cmdline-tools/latest" \
    && rm -rf /tmp/cmdline-tools.zip /tmp/cmdline-tools

# ---- SDK packages + AVD ------------------------------------------------------
RUN yes | sdkmanager --licenses > /dev/null \
    && sdkmanager --install \
        "platform-tools" \
        "emulator" \
        "platforms;android-${ANDROID_API}" \
        "${SYSTEM_IMAGE}" > /dev/null \
    && echo "no" | avdmanager create avd \
        --force \
        --name "${AVD_NAME}" \
        --package "${SYSTEM_IMAGE}" \
        --device "pixel_7_pro" \
    && avd_cfg="${ANDROID_AVD_HOME}/${AVD_NAME}.avd/config.ini" \
    && sed -i '/^hw\.lcd\.width=/d; /^hw\.lcd\.height=/d; /^hw\.lcd\.density=/d' "${avd_cfg}" \
    && printf 'hw.lcd.width=720\nhw.lcd.height=1600\nhw.lcd.density=320\n' >> "${avd_cfg}"

# ---- Challenge payload -------------------------------------------------------
# Everything challenge-specific lives in ./challenge/ (next to this Dockerfile):
# setup.sh (provisioning, invoked by start.sh) plus your apks/flags/assets. It
# all lands in /opt/challenge, referenced from setup.sh as $CHALLENGE_DIR.
RUN mkdir -p /opt/challenge
COPY challenge/ /opt/challenge/

# ---- Entrypoint --------------------------------------------------------------
# start.sh = generic emulator/ADB/lockdown orchestration.
COPY start.sh /usr/local/bin/start.sh
# strip CRLF in case the scripts were saved with Windows line endings
RUN sed -i 's/\r$//' /usr/local/bin/start.sh && chmod +x /usr/local/bin/start.sh \
    && if [ -f /opt/challenge/setup.sh ]; then \
         sed -i 's/\r$//' /opt/challenge/setup.sh && chmod +x /opt/challenge/setup.sh; \
       fi

# console (emulator), adb transport (published), adb server
EXPOSE 5555

ENTRYPOINT ["/usr/local/bin/start.sh"]
