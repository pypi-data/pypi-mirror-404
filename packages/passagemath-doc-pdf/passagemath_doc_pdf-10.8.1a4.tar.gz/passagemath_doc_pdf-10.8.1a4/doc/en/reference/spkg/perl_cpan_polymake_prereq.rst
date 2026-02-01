.. _spkg_perl_cpan_polymake_prereq:

perl_cpan_polymake_prereq: Represents all Perl packages that are prerequisites for polymake
===========================================================================================

Description
-----------

This script package represents all Perl packages that are prerequisites
for polymake.

License
-------

Various free software licenses


Type
----

optional


Dependencies
------------

- :ref:`spkg_perl_app_perlbrew`


Installation commands
---------------------

.. tab:: Sage distribution:

   .. CODE-BLOCK:: bash

       $ sage -i perl_cpan_polymake_prereq

.. tab:: Alpine:

   .. CODE-BLOCK:: bash

       $ apk add perl-term-readkey perl-dev perl-json perl-xml-writer \
             perl-xml-libxslt

.. tab:: Arch Linux:

   .. CODE-BLOCK:: bash

       $ sudo pacman -S perl-json perl-term-readkey perl-xml-libxml \
             perl-xml-libxslt perl-xml-writer

.. tab:: cpan:

   .. CODE-BLOCK:: bash

       $ cpan -i XML::Writer XML::SAX JSON SVG Term::ReadKey

.. tab:: Debian/Ubuntu:

   .. CODE-BLOCK:: bash

       $ sudo apt-get install libxml-libxslt-perl libxml-writer-perl \
             libxml2-dev libperl-dev libjson-perl libsvg-perl \
             libterm-readkey-perl libterm-readline-gnu-perl

.. tab:: Fedora/Redhat/CentOS:

   .. CODE-BLOCK:: bash

       $ sudo dnf install perl-ExtUtils-Embed perl-JSON perl-Term-ReadLine-Gnu \
             perl-TermReadKey perl-XML-Writer perl-XML-LibXML perl-XML-LibXSLT \
             perl-SVG

.. tab:: FreeBSD:

   .. CODE-BLOCK:: bash

       $ sudo pkg install textproc/p5-XML-Writer textproc/p5-XML-LibXML \
             textproc/p5-XML-LibXSLT converters/p5-JSON textproc/p5-SVG \
             devel/p5-Term-ReadKey

.. tab:: Gentoo Linux:

   .. CODE-BLOCK:: bash

       $ sudo emerge XML-Writer XML-LibXML XML-LibXSLT \
             dev-perl/Term-ReadLine-Gnu dev-perl/TermReadKey JSON SVG

.. tab:: Nixpkgs:

   .. CODE-BLOCK:: bash

       $ nix-env -f \'\<nixpkgs\>\' --install --attr perlPackages.XMLWriter perlPackages.XMLLibXML perlPackages.XMLLibXSLT perlPackages.JSON perlPackages.TermReadKey

.. tab:: openSUSE:

   .. CODE-BLOCK:: bash

       $ sudo zypper install perl-XML-Writer perl-XML-LibXML perl-XML-LibXSLT \
             perl-JSON perl-SVG perl-Term-ReadKey

.. tab:: Void Linux:

   .. CODE-BLOCK:: bash

       $ sudo xbps-install perl-JSON perl-SVG perl-Term-ReadKey \
             perl-XML-LibXML perl-XML-LibXSLT perl-XML-Writer


However, these system packages will not be used for building Sage
because ``spkg-configure.m4`` has not been written for this package;
see :issue:`27330` for more information.
