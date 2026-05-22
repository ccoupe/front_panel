#
# Makefile for tblogin - trumpybear front panel gui
#
PRJ ?= tblogin
DESTDIR ?= /usr/local/lib/tblogin
SRCDIR ?= $(HOME)/Projects/iot/tblogin
LAUNCH ?= tblogin.sh
SERVICE ?=$(PRJ).service
PYENV ?= ${DESTDIR}/.venv
PYVER ?= 3.11.2

NODE := $(shell hostname)
SHELL := /bin/bash 

${PYENV}: ${SRCDIR}/requirements.txt
	sudo mkdir -p ${DESTDIR}
	sudo chown ${USER} ${DESTDIR}
	uv venv --python ${PYVER} --no-project ${PYENV}
	( \
	set -e ;\
	source ${PYENV}/bin/activate ; \
	sudo apt-get install python3-pil python3-pil.imagetk ; \
	uv pip install -r $(SRCDIR)/requirements.txt ; \
	)

setup_launch:
	systemctl --user enable ${SERVICE}
	systemctl --user daemon-reload
	systemctl --user restart ${SERVICE}

setup_dir:
	sudo mkdir -p ${DESTDIR}
	sudo mkdir -p ${DESTDIR}/images
	sudo cp ${SRCDIR}/images/* ${DESTDIR}/images
	sudo cp ${SRCDIR}/Makefile ${DESTDIR}
	sudo cp ${SRCDIR}/${NODE}.json ${DESTDIR}
	sudo cp ${SRCDIR}/requirements.txt ${DESTDIR}
	sudo cp ${SRCDIR}/${SERVICE} ${DESTDIR}
	sudo chown -R ${USER} ${DESTDIR}
	sed  s!PYENV!${PYENV}! <${SRCDIR}/launch.sh >$(DESTDIR)/$(LAUNCH)
	sudo chmod +x ${DESTDIR}/${LAUNCH}
	mkdir -p $(HOME)/.config/systemd/user
	sudo cp ${DESTDIR}/${SERVICE} /etc/xdg/systemd/user
	systemctl --user enable ${SERVICE}
	systemctl --user daemon-reload
	systemctl --user restart ${SERVICE}
	
install: ${PYENV} setup_dir update setup_launch

update: 
	sudo cp ${SRCDIR}/Homie_MQTT.py ${DESTDIR}
	sudo cp ${SRCDIR}/TurretSlider.py ${DESTDIR}
	sudo cp ${SRCDIR}/Settings.py ${DESTDIR}
	sudo cp ${SRCDIR}/login.py ${DESTDIR}
	sudo cp ${SRCDIR}/${NODE}.json ${DESTDIR}
	sudo cp ${SRCDIR}/${SERVICE} ${DESTDIR}
	sudo chown -R ${USER} ${DESTDIR}

lint:
	 flake8 --indent-size 2 --max-line-length 90 --ignore=W293,F824 \
--exclude .venv,${PYENV}


clean: 
	systemctl --user stop ${SERVICE}
	systemctl --user disable ${SERVICE}
	rm -f ${HOME}/.config/systemd/user/${SERVICE}
	sudo rm -rf ${DESTDIR}

realclean: clean
	rm -rf ${PYENV}
