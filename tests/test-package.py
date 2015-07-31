# Import stock packages
import re

#
# Test methods to make sure the package is properly generated
#
class TestUtilsClass:  

    #
    # Make sure requirements in setup.py and requirements.txt match
    #
    def test_requirements(self):
        requirements_from_file = []
        with open('requirements.txt', 'rt') as f:
            for requirement in f.readlines():
                requirements_from_file.append(requirement.strip())
        requirements_from_setup = []
        with open('setup.py', 'rt') as f:
            for requirement in re.findall(r'requirements = \[(.*?)\]', f.read(), re.DOTALL|re.MULTILINE)[0].splitlines():
                requirement = re.sub(r',$', '', requirement).replace('\'', '').strip()
                if requirement:
                    requirements_from_setup.append(requirement)
        assert len(requirements_from_file) == len(requirements_from_setup) == len(set(requirements_from_file) & set(requirements_from_setup))
