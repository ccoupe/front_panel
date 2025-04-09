#
# Makefile for 'alarm' aka mqttalarm
#
PRJ ?= login
DESTDIR ?= /usr/local/lib/tblogin
SRCDIR ?= $(HOME)/Projects/iot/login
LAUNCH ?= tblogin.sh
SERVICE ?=tb$(PRJ).service
PYENV ?= ${DESTDIR}/tb-env

NODE := $(shell hostname)
SHELL := /bin/bash 

${PYENV}:
	sudo mkdir -p ${PYENV}
	sudo chown ${USER} ${PYENV}
	sudo apt-get install python3-pil python3-pil.imagetk
	python3 -m venv --system-site-packages ${PYENV}
	( \
	set -e ;\
	source ${PYENV}/bin/activate; \
	pip install -r $(SRCDIR)/requirements.txt; \
	)

setup_launch:
	systemctl --user enable ${SERVICE}
	systemctl --user daemon-reload
	systemctl --user restart ${SERVICE}

setup_dir:
	sudo mkdir -p ${DESTDIR}
	sudo mkdir -p ${DESTDIR}/lib	
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
	sudo cp ${SRCDIR}/lib/Homie_MQTT.py ${DESTDIR}/lib
	sudo cp ${SRCDIR}/lib/TurretSlider.py ${DESTDIR}/lib
	sudo cp ${SRCDIR}/lib/Settings.py ${DESTDIR}/lib
	sudo cp ${SRCDIR}/login.py ${DESTDIR}
	sudo cp ${SRCDIR}/${NODE}.json ${DESTDIR}
	sudo cp ${SRCDIR}/${SERVICE} ${DESTDIR}
	sudo chown -R ${USER} ${DESTDIR}



clean: 
	systemctl --user stop ${SERVICE}
	systemctl --user disable ${SERVICE}
	rm -f ${HOME}/.config/systemd/user/${SERVICE}
	sudo rm -rf ${DESTDIR}

realclean: clean
	rm -rf ${PYENV}
