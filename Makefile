#
# Makefile for tblogin - trumpybear front panel gui
#
PRJ ?= tblogin
DESTDIR ?= /usr/local/lib/tblogin
SRCDIR ?= $(HOME)/Projects/iot/tblogin
LAUNCH ?= tblogin.sh
SERVICE ?=$(PRJ).service
PYENV ?= ${DESTDIR}/.venv
PYVER ?= 3.13.5

NODE := $(shell hostname)
SHELL := /bin/bash 

# Define function; $(1) is the python file name.
define copyheader =
$(DESTDIR)/$(1): $(SRCDIR)/$(1)
	cp -u $$^ $$@
endef

# Use function to create recipes for each python file.
$(foreach file,$(PYFILES),$(eval $(call copyheader,$(file))))

${PYENV}: ${SRCDIR}/requirements.txt
	sudo mkdir -p ${DESTDIR}
	sudo chown ${USER} ${DESTDIR}
	uv venv --python ${PYVER} --no-project ${PYENV}
	( \
	set -e ;\
	source ${PYENV}/bin/activate ; \
	sudo apt-get update ; \
	sudo apt-get install -y python3-pil python3-pil.imagetk ; \
	uv pip install --upgrade pip ; \
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
	
# Get all Python files in the source directory
PYFILES = $(shell cd $(SRCDIR); ls *.py)

install: ${PYENV} setup_dir update setup_launch

update: 
	# Update Python files using the copyheader function
	# Copy other non-Python files
	sudo cp -u ${SRCDIR}/Homie_MQTT.py ${DESTDIR}
	sudo cp -u ${SRCDIR}/TurretSlider.py ${DESTDIR}
	sudo cp -u ${SRCDIR}/Settings.py ${DESTDIR}
	sudo cp -u ${SRCDIR}/login.py ${DESTDIR}
	sudo cp -u ${SRCDIR}/${NODE}.json ${DESTDIR}
	sudo cp -u ${SRCDIR}/${SERVICE} ${DESTDIR}
	sudo chown -R ${USER} ${DESTDIR}
	# Reinstall dependencies in the virtual environment
	( \
	set -e ;\
	source ${PYENV}/bin/activate ; \
	uv pip install --upgrade -r $(SRCDIR)/requirements.txt ; \
	)

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