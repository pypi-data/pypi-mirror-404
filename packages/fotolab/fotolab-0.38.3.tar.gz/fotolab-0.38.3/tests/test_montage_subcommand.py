# Copyright (C) 2024,2025,2026 Kian-Meng Ang

# This program is free software: you can redistribute it and/or modify it under
# the terms of the GNU Affero General Public License as published by the Free
# Software Foundation, either version 3 of the License, or (at your option) any
# later version.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. See the GNU Affero General Public License for more
# details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program. If not, see <https://www.gnu.org/licenses/>.


from PIL import Image


def test_montage_subcommand(cli_runner, image_file):
    img_path = image_file("sample.png")
    ret = cli_runner("montage", str(img_path), str(img_path))
    assert ret.returncode == 0


def test_montage_subcommand_with_single_image_raises_error(
    cli_runner,
    image_file,
):
    img_path = image_file("sample.png")
    ret = cli_runner("montage", str(img_path))
    assert ret.returncode != 0
    assert "error: at least two images is required for montage" in ret.stdout


def test_montage_subcommand_with_border(cli_runner, image_file, tmp_path):
    img_path = image_file("sample.png")

    with Image.open(img_path) as img:
        orig_width, orig_height = img.size

    border_width = 10
    ret = cli_runner(
        "montage",
        "-b",
        str(border_width),
        str(img_path),
        str(img_path),
    )
    assert ret.returncode == 0

    full_output_path = (
        tmp_path / "scripttest" / "output" / "montage_sample.png"
    )

    assert full_output_path.exists()

    with Image.open(full_output_path) as img:
        width, height = img.size

        expected_width = 2 * (orig_width + 2 * border_width)
        expected_height = orig_height + 2 * border_width

        assert width == expected_width
        assert height == expected_height


def test_montage_subcommand_with_border_and_color(
    cli_runner,
    image_file,
    tmp_path,
):
    img_path = image_file("sample.png")
    border_width = 5
    border_color = "red"
    ret = cli_runner(
        "montage",
        "-b",
        str(border_width),
        "-bc",
        border_color,
        str(img_path),
        str(img_path),
    )
    assert ret.returncode == 0

    full_output_path = (
        tmp_path / "scripttest" / "output" / "montage_sample.png"
    )
    assert full_output_path.exists()

    with Image.open(full_output_path) as img:
        # check a pixel that should be in the border (top-left corner)
        # if image is RGBA, it might return (255, 0, 0, 255)
        pixel = img.getpixel((0, 0))
        assert pixel[:3] == (255, 0, 0)
