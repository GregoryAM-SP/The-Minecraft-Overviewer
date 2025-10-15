FROM python:3.8.19-bullseye AS build

WORKDIR /usr/overviewer
COPY . /usr/overviewer/

RUN pip3 install -r requirements.txt

# Copy required c headers
RUN curl -o Imaging.h https://raw.githubusercontent.com/python-pillow/Pillow/10.2.0/src/libImaging/Imaging.h
RUN curl -o ImagingUtils.h https://raw.githubusercontent.com/python-pillow/Pillow/10.2.0/src/libImaging/ImagingUtils.h
RUN curl -o ImPlatform.h https://raw.githubusercontent.com/python-pillow/Pillow/10.2.0/src/libImaging/ImPlatform.h

# Build
RUN python setup.py build
RUN pyinstaller overviewer.spec

# I've tried with alpine and distroless images, but there was a problem with missing libs.
FROM debian:12.5-slim
WORKDIR /usr/overviewer
COPY --from=build /usr/overviewer/dist/overviewer /usr/overviewer
USER 1000:1000
ENTRYPOINT ["/usr/overviewer/overviewer"]