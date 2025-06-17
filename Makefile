#
# Makefile for 'alarm' aka mqttalarm
#
PRJ ?= tblogin
DESTDIR ?= /usr/local/lib/tblogin
SRCDIR ?= $(HOME)/Projects/iot/tblogin
LAUNCH ?= tblogin.sh
SERVICE ?=$(PRJ).service
PYENV ?= ${DESTDIR}/.venv

NODE := $(shell hostname)
SHELL := /bin/bash 

${PYENV}: ${SRCDIR}/requirements.txt
	sudo mkdir -p ${DESTDIR}
	sudo chown ${USER} ${DESTDIR}
	sudo cp ${SRCDIR}/pyproject.toml ${DESTDIR}
	uv python pin 3.11.2
	uv venv --system-site-packages ${PYENV}
	source ${PYENV}/bin/activate
	uv python pin 3.11.2
	sudo apt-get install python3-pil python3-pil.imagetk
	uv add -r $(SRCDIR)/requirements.txt

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
	sudo cp ${SRCDIR}/main.py ${DESTDIR}
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
