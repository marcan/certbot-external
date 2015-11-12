"""External Configuration"""
import logging
import os
import subprocess

import zope.interface

from acme import challenges

from letsencrypt import errors
from letsencrypt import interfaces
from letsencrypt import reverter

from letsencrypt.plugins import common

from letsencrypt_external import constants
from letsencrypt_external import dvsni

logger = logging.getLogger(__name__)


class ExternalConfigurator(common.Plugin):
    """External configurator."""
    zope.interface.implements(interfaces.IAuthenticator)
    zope.interface.classProvides(interfaces.IPluginFactory)

    description = "Configuration via external shell script"

    @classmethod
    def add_parser_arguments(cls, add):
        add("handler", default=constants.CLI_DEFAULTS["handler"],
            help="External handler script path.")

    def __init__(self, *args, **kwargs):
        """Initialize an External Configurator."""
        super(ExternalConfigurator, self).__init__(*args, **kwargs)

        # Set up reverter
        self.reverter = reverter.Reverter(self.config)
        self.reverter.recovery_routine()

    # This is called in determine_authenticator and determine_installer
    def prepare(self):
        """Prepare the authenticator/installer."""
        pass

    def get_chall_pref(self, domain):
        """Return list of challenge preferences.

        :param str domain: Domain for which challenge preferences are sought.

        :returns: List of challenge types (subclasses of
            :class:`acme.challenges.Challenge`) with the most
            preferred challenges first. If a type is not specified, it means the
            Authenticator cannot perform the challenge.
        :rtype: list

        """
        return [challenges.TLSSNI01]

    def perform(self, achalls):
        """Perform the given challenge.

        :param list achalls: Non-empty (guaranteed) list of
            :class:`~letsencrypt.achallenges.AnnotatedChallenge`
            instances, such that it contains types found within
            :func:`get_chall_pref` only.

        :returns: List of ACME
            :class:`~acme.challenges.ChallengeResponse` instances
            or if the :class:`~acme.challenges.Challenge` cannot
            be fulfilled then:

            ``None``
              Authenticator can perform challenge, but not at this time.
            ``False``
              Authenticator will never be able to perform (error).

        :rtype: :class:`list` of
            :class:`acme.challenges.ChallengeResponse`

        :raises .PluginError: If challenges cannot be performed

        """
        external_dvsni = dvsni.ExternalDvsni(self)

        responses = []

        if self.call_handler("pre-perform") is None:
            raise errors.PluginError("pre-perform handler failed")

        for i, achall in enumerate(achalls):
            responses.append(None)

            external_dvsni.add_chall(achall, i)

        sni_response = external_dvsni.perform()

        if self.call_handler("post-perform") is None:
            raise errors.PluginError("post-perform handler failed")

        # Go through all of the challenges and assign them to the proper place
        # in the responses return value. All responses must be in the same order
        # as the original challenges.
        for i, resp in enumerate(sni_response):
            responses[external_dvsni.indices[i]] = resp

        return responses

    def cleanup(self, achalls):
        """Revert changes and shutdown after challenges complete.

        :param list achalls: Non-empty (guaranteed) list of
            :class:`~letsencrypt.achallenges.AnnotatedChallenge`
            instances, a subset of those previously passed to :func:`perform`.

        :raises PluginError: if original configuration cannot be restored

        """
        if self.call_handler("pre-cleanup") is None:
            raise errors.PluginError("pre-cleanup handler failed")

        for i, achall in enumerate(achalls):
            if self.call_handler("cleanup", domain=achall.domain) is None:
                raise errors.PluginError("cleanup handler failed")

        if self.call_handler("post-cleanup") is None:
            raise errors.PluginError("post-cleanup handler failed")

    def more_info(self):
        """Human-readable string to help understand the module"""
        return (
            "Uses an external shell script to authenticate and deploy "
            "certificates.{0}"
            "External handler path: {handler}".format(
                os.linesep, handler=self.conf('handler'))
        )

    def call_handler(self, command, *args, **kwargs):
        env = dict(os.environ)
        env.update(kwargs)
        proc = subprocess.Popen([self.conf('handler'), command] + list(args),
                                stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE,
                                env=env)
        stdout, stderr = proc.communicate()

        if proc.returncode != 0:
            if stdout.strip() == "NotImplemented":
                logger.warning("Handler script does not implement %s\n%s",
                               command, stderr)
                return NotImplemented
            else:
                logger.error("Handler script failed!\n%s\n%s", stdout, stderr)
                return None
        else:
                logger.info("Handler output (%s):\n%s\n%s",
                               command, stdout, stderr)
        return stdout
